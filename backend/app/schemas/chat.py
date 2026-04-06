"""
对话 Schema

对话相关的 Pydantic 模型定义
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field




class Message(BaseModel):
    """消息模型"""
    role: Literal["system", "user", "assistant", "tool"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    name: Optional[str] = Field(default=None, description="工具调用时的工具名")
    tool_calls: Optional[List[dict]] = Field(default=None, description="工具调用请求")
    tool_call_id: Optional[str] = Field(default=None, description="工具调用ID")
    timestamp: Optional[str] = Field(default=None, description="消息时间戳")


class ChatRequest(BaseModel):
    """对话请求"""
    preset_id: str = Field(..., description="使用的预设方案ID")
    message: str = Field(..., min_length=1, description="用户消息")
    session_id: Optional[str] = Field(default=None, description="会话ID，为空则创建新会话")
    stream: bool = Field(default=True, description="是否流式输出")
    enable_tools: bool = Field(default=True, description="是否启用工具调用（默认启用）")
    enable_rag: bool = Field(default=True, description="是否启用知识库检索（默认启用）")
    enable_memory: bool = Field(default=True, description="是否启用记忆系统（默认启用）")
    # 多平台支持
    channel_type: str = Field(default="web", description="平台类型: web, qq, qq_group, qq_private, feishu, dingtalk, telegram")
    channel_id: Optional[str] = Field(default=None, description="平台特定ID: QQ号/群号、飞书用户ID等")


class ChatResponse(BaseModel):
    """对话响应"""
    content: str = Field(..., description="AI回复内容")
    session_id: str = Field(..., description="会话ID")
    usage: Optional[dict] = Field(default=None, description="Token使用情况")


class ChatStreamChunk(BaseModel):
    """流式对话块"""
    content: str = Field(..., description="内容块")
    is_end: bool = Field(default=False, description="是否结束")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class ConversationInDB(BaseModel):
    """数据库中的对话记录"""
    id: int
    session_id: str
    channel_type: str = Field(default="web", description="平台类型")
    channel_id: Optional[str] = Field(default=None, description="平台特定ID")
    preset_id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ConversationDetail(ConversationInDB):
    """对话详情"""
    messages: List[Message] = Field(default_factory=list)


class ConversationList(BaseModel):
    """对话列表项"""
    id: int
    session_id: str
    channel_type: str = Field(default="web", description="平台类型")
    channel_id: Optional[str] = Field(default=None, description="平台特定ID")
    preset_id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str


class ConversationCreate(BaseModel):
    """创建对话请求"""
    preset_id: str
    title: Optional[str] = Field(default="新对话", max_length=256)


class ConversationUpdate(BaseModel):
    """更新对话请求"""
    title: Optional[str] = Field(default=None, max_length=256)


class FeedbackRequest(BaseModel):
    """用户反馈请求"""
    message_index: int = Field(..., description="消息索引")
    feedback: Literal["like", "dislike"] = Field(..., description="反馈类型")
    comment: Optional[str] = Field(default=None, description="评论")
