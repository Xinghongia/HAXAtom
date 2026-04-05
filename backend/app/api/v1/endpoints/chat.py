"""
对话 API

提供对话相关的 RESTful 接口
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core import PresetEngine
from app.db import get_db
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    ConversationCreate,
    ConversationDetail,
    ConversationList,
    ConversationUpdate,
    ResponseBase,
)
from app.services import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/completions")
async def chat_completion(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    对话补全（非流式）
    
    根据预设方案执行对话，返回完整响应
    自动保存对话历史，支持记忆系统
    """
    engine = PresetEngine(db)
    conv_service = ConversationService(db)
    
    try:
        # 获取或创建对话（支持多平台）
        if request.session_id:
            conversation = await conv_service.get_conversation(request.session_id)
            if not conversation:
                conversation = await conv_service.create_conversation(
                    preset_id=request.preset_id,
                    session_id=request.session_id,
                    channel_type=request.channel_type,
                    channel_id=request.channel_id
                )
        else:
            conversation = await conv_service.create_conversation(
                preset_id=request.preset_id,
                channel_type=request.channel_type,
                channel_id=request.channel_id
            )
        
        session_id = conversation.session_id
        
        # 保存用户消息
        await conv_service.add_message(session_id, "user", request.message)
        
        # 执行对话（非流式）
        # 如果启用了记忆系统，不需要传入history，引擎会自动从记忆服务获取
        response_chunks = []
        async for chunk in engine.chat(
            preset_id=request.preset_id,
            message=request.message,
            session_id=session_id,  # 传入session_id用于记忆检索
            history=None,  # 优先使用记忆系统
            stream=False,
            enable_tools=request.enable_tools,
            enable_rag=request.enable_rag,
            enable_memory=request.enable_memory
        ):
            response_chunks.append(chunk)
        
        full_response = "".join(response_chunks)
        
        # 保存AI回复
        await conv_service.add_message(session_id, "assistant", full_response)
        
        return ResponseBase(
            data=ChatResponse(
                content=full_response,
                session_id=session_id,
                usage=None
            )
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/completions/stream")
async def chat_completion_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    对话补全（流式/SSE）
    
    根据预设方案执行对话，返回SSE流式响应
    自动保存对话历史，支持记忆系统
    """
    engine = PresetEngine(db)
    conv_service = ConversationService(db)
    
    # 获取或创建对话（支持多平台）
    if request.session_id:
        conversation = await conv_service.get_conversation(request.session_id)
        if not conversation:
            conversation = await conv_service.create_conversation(
                preset_id=request.preset_id,
                session_id=request.session_id,
                channel_type=request.channel_type,
                channel_id=request.channel_id
            )
    else:
        conversation = await conv_service.create_conversation(
            preset_id=request.preset_id,
            channel_type=request.channel_type,
            channel_id=request.channel_id
        )
    
    session_id = conversation.session_id
    
    # 保存用户消息
    await conv_service.add_message(session_id, "user", request.message)
    
    logger.info(f"[chat_completion_stream] 请求参数：enable_memory={request.enable_memory}, enable_tools={request.enable_tools}, enable_rag={request.enable_rag}")
    
    async def event_generator():
        full_response = []
        
        try:
            async for chunk in engine.chat(
                preset_id=request.preset_id,
                message=request.message,
                session_id=session_id,  # 传入 session_id 用于记忆检索
                history=None,  # 优先使用记忆系统
                stream=True,
                enable_tools=request.enable_tools,
                enable_rag=request.enable_rag,
                enable_memory=request.enable_memory
            ):
                full_response.append(chunk)
                yield {
                    "event": "message",
                    "data": ChatStreamChunk(content=chunk).model_dump_json()
                }
            
            # 保存完整 AI 回复
            full_text = "".join(full_response)
            await conv_service.add_message(session_id, "assistant", full_text)
            
            # 发送结束标记
            yield {
                "event": "message",
                "data": ChatStreamChunk(content="", is_end=True).model_dump_json()
            }
        
        except Exception as e:
            logger.error(f"[chat_completion_stream] 错误：{e}", exc_info=True)
            yield {
                "event": "error",
                "data": str(e)
            }
    
    return EventSourceResponse(event_generator())


# ==================== 对话管理接口 ====================

@router.get("/conversations", response_model=ResponseBase[List[ConversationList]])
async def list_conversations(
    preset_id: Optional[str] = Query(None, description="按预设方案筛选"),
    channel_type: Optional[str] = Query(None, description="按平台类型筛选: web, qq, feishu等"),
    channel_id: Optional[str] = Query(None, description="按平台ID筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话列表
    
    支持按平台类型和平台ID筛选
    按更新时间倒序排列
    """
    conv_service = ConversationService(db)
    conversations = await conv_service.list_conversations(
        preset_id=preset_id,
        channel_type=channel_type,
        channel_id=channel_id,
        skip=skip,
        limit=limit
    )
    
    logger.info(f"[list_conversations] 返回 {len(conversations)} 条会话")
    
    return ResponseBase(data=[
        ConversationList(
            id=conv.id,
            session_id=conv.session_id,
            channel_type=conv.channel_type,
            channel_id=conv.channel_id,
            preset_id=conv.preset_id,
            title=conv.title,
            message_count=conv.message_count,
            created_at=conv.created_at.isoformat() if conv.created_at else "",
            updated_at=conv.updated_at.isoformat() if conv.updated_at else ""
        ) for conv in conversations
    ])


@router.get("/conversations/{session_id}", response_model=ResponseBase[ConversationDetail])
async def get_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话详情
    
    包含完整的对话消息历史
    """
    conv_service = ConversationService(db)
    conversation = await conv_service.get_conversation(session_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    from app.schemas.chat import Message
    
    messages = [
        Message(
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            name=msg.get("name"),
            tool_calls=msg.get("tool_calls"),
            tool_call_id=msg.get("tool_call_id"),
            timestamp=msg.get("timestamp")
        ) for msg in (conversation.messages or [])
    ]
    
    return ResponseBase(data=ConversationDetail(
        id=conversation.id,
        session_id=conversation.session_id,
        channel_type=conversation.channel_type,
        channel_id=conversation.channel_id,
        preset_id=conversation.preset_id,
        title=conversation.title,
        message_count=conversation.message_count,
        created_at=conversation.created_at.isoformat() if conversation.created_at else "",
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
        messages=messages
    ))


@router.post("/conversations", response_model=ResponseBase[ConversationDetail])
async def create_conversation(
    request: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新对话
    """
    conv_service = ConversationService(db)
    conversation = await conv_service.create_conversation(
        preset_id=request.preset_id,
        title=request.title
    )
    
    return ResponseBase(data=ConversationDetail(
        id=conversation.id,
        session_id=conversation.session_id,
        preset_id=conversation.preset_id,
        title=conversation.title,
        message_count=0,
        created_at=conversation.created_at.isoformat() if conversation.created_at else "",
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
        messages=[]
    ))


@router.put("/conversations/{session_id}", response_model=ResponseBase[ConversationDetail])
async def update_conversation(
    session_id: str,
    request: ConversationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新对话信息（目前仅支持修改标题）
    """
    conv_service = ConversationService(db)
    
    if request.title:
        try:
            conversation = await conv_service.update_title(session_id, request.title)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        conversation = await conv_service.get_conversation(session_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    
    from app.schemas.chat import Message
    
    messages = [
        Message(
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            name=msg.get("name"),
            tool_calls=msg.get("tool_calls"),
            tool_call_id=msg.get("tool_call_id"),
            timestamp=msg.get("timestamp")
        ) for msg in (conversation.messages or [])
    ]

    return ResponseBase(data=ConversationDetail(
        id=conversation.id,
        session_id=conversation.session_id,
        preset_id=conversation.preset_id,
        title=conversation.title,
        message_count=conversation.message_count,
        created_at=conversation.created_at.isoformat() if conversation.created_at else "",
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
        messages=messages
    ))


@router.post("/conversations/{session_id}/clear", response_model=ResponseBase[ConversationDetail])
async def clear_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    清空对话消息（保留对话记录）
    """
    conv_service = ConversationService(db)
    
    try:
        conversation = await conv_service.clear_messages(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return ResponseBase(data=ConversationDetail(
        id=conversation.id,
        session_id=conversation.session_id,
        preset_id=conversation.preset_id,
        title=conversation.title,
        message_count=0,
        created_at=conversation.created_at.isoformat() if conversation.created_at else "",
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
        messages=[]
    ))


@router.delete("/conversations/{session_id}", response_model=ResponseBase[dict])
async def delete_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除对话（永久删除）
    """
    conv_service = ConversationService(db)
    success = await conv_service.delete_conversation(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ResponseBase(data={"deleted": True, "session_id": session_id})
