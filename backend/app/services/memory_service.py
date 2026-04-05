"""
记忆服务

提供对话记忆管理功能：
- 短期记忆（对话窗口）
- 长期记忆（对话摘要）
- 记忆检索和注入
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MemoryConfig, Conversation
from app.schemas.memory_config import MemoryConfigCreate, MemoryConfigUpdate


class MemoryService:
    """
    记忆服务类
    
    管理对话的记忆功能，支持多种记忆类型
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== 记忆配置管理 ====================
    
    async def create_memory_config(self, data: MemoryConfigCreate) -> MemoryConfig:
        """
        创建记忆配置
        
        Args:
            data: 记忆配置创建数据
            
        Returns:
            MemoryConfig: 创建的记忆配置对象
        """
        import uuid
        
        memory_id = f"mem_{uuid.uuid4().hex[:8]}"
        
        config = MemoryConfig(
            memory_id=memory_id,
            memory_name=data.memory_name,
            memory_type=data.memory_type,
            memory_params=data.memory_params or {}
        )
        
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        
        return config
    
    async def get_memory_config(self, memory_id: str) -> Optional[MemoryConfig]:
        """
        获取记忆配置
        
        Args:
            memory_id: 记忆配置ID
            
        Returns:
            Optional[MemoryConfig]: 记忆配置对象或None
        """
        result = await self.db.execute(
            select(MemoryConfig).where(
                MemoryConfig.memory_id == memory_id,
                MemoryConfig.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def list_memory_configs(self, skip: int = 0, limit: int = 100) -> List[MemoryConfig]:
        """
        获取记忆配置列表
        
        Args:
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            List[MemoryConfig]: 记忆配置列表
        """
        result = await self.db.execute(
            select(MemoryConfig)
            .where(MemoryConfig.is_active == True)
            .order_by(MemoryConfig.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update_memory_config(
        self,
        memory_id: str,
        data: MemoryConfigUpdate
    ) -> Optional[MemoryConfig]:
        """
        更新记忆配置
        
        Args:
            memory_id: 记忆配置ID
            data: 更新数据
            
        Returns:
            Optional[MemoryConfig]: 更新后的记忆配置对象
        """
        config = await self.get_memory_config(memory_id)
        if not config:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return config
    
    async def delete_memory_config(self, memory_id: str) -> bool:
        """
        删除记忆配置（软删除）
        
        Args:
            memory_id: 记忆配置ID
            
        Returns:
            bool: 是否成功删除
        """
        config = await self.get_memory_config(memory_id)
        if not config:
            return False
        
        config.is_active = False
        await self.db.commit()
        
        return True
    
    # ==================== 对话记忆管理 ====================
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            session_id: 会话ID
            limit: 返回消息数量限制
            
        Returns:
            List[Dict]: 消息列表
        """
        from app.services import ConversationService
        
        conv_service = ConversationService(self.db)
        conversation = await conv_service.get_conversation(session_id)
        
        if not conversation:
            return []
        
        # 获取最近的消息
        messages = conversation.messages or []
        from app.main import logger
        logger.info(f"[MemoryService] 加载会话 {session_id} 历史：共 {len(messages)} 条消息，返回最近 {min(limit, len(messages))} 条")
        return messages[-limit:] if len(messages) > limit else messages
    
    async def get_formatted_history(
        self,
        session_id: str,
        memory_type: str = "buffer_window",
        memory_params: Optional[Dict] = None
    ) -> str:
        """
        获取格式化的对话历史（用于注入提示词）
        
        Args:
            session_id: 会话ID
            memory_type: 记忆类型
            memory_params: 记忆参数
            
        Returns:
            str: 格式化的历史对话文本
        """
        if memory_params is None:
            memory_params = {}
        
        if memory_type == "buffer_window":
            # 滑动窗口记忆 - 返回最近N条消息
            window_size = memory_params.get("window_size", 10)
            messages = await self.get_conversation_history(session_id, limit=window_size)
            
        elif memory_type == "summary":
            # 摘要记忆 - 返回对话摘要（简化实现）
            return await self._get_conversation_summary(session_id)
            
        elif memory_type == "token_buffer":
            # Token限制记忆
            max_tokens = memory_params.get("max_tokens", 2000)
            messages = await self._get_messages_by_token_limit(session_id, max_tokens)
            
        else:
            # 默认使用滑动窗口
            messages = await self.get_conversation_history(session_id, limit=10)
        
        # 格式化为文本
        return self._format_messages(messages)
    
    def _format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """
        将消息列表格式化为文本
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 格式化后的文本
        """
        if not messages:
            return ""
        
        formatted = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                formatted.append(f"用户: {content}")
            elif role == "assistant":
                formatted.append(f"助手: {content}")
            elif role == "system":
                formatted.append(f"系统: {content}")
        
        return "\n\n".join(formatted)
    
    async def _get_conversation_summary(self, session_id: str) -> str:
        """
        获取对话摘要（简化版）
        
        实际项目中可以使用LLM生成摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            str: 对话摘要
        """
        messages = await self.get_conversation_history(session_id, limit=50)
        
        if not messages:
            return ""
        
        # 简化摘要：统计消息数量和主要话题
        user_msgs = [m for m in messages if m.get("role") == "user"]
        
        if len(user_msgs) <= 3:
            # 消息较少，返回完整历史
            return self._format_messages(messages)
        
        # 消息较多，返回摘要
        summary = f"对话历史摘要：\n"
        summary += f"- 共 {len(messages)} 条消息\n"
        summary += f"- 用户提问 {len(user_msgs)} 次\n"
        summary += f"- 最近话题涉及：{user_msgs[-1].get('content', '')[:50]}...\n"
        summary += f"\n最近对话：\n{self._format_messages(messages[-6:])}"
        
        return summary
    
    async def _get_messages_by_token_limit(
        self,
        session_id: str,
        max_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        根据Token限制获取消息
        
        简化实现：假设平均每个字符0.5个token
        
        Args:
            session_id: 会话ID
            max_tokens: 最大Token数
            
        Returns:
            List[Dict]: 消息列表
        """
        all_messages = await self.get_conversation_history(session_id, limit=100)
        
        if not all_messages:
            return []
        
        # 从后往前累加，直到达到token限制
        selected_messages = []
        current_tokens = 0
        
        for msg in reversed(all_messages):
            content = msg.get("content", "")
            # 简化估算：1个汉字 ≈ 1 token，1个英文单词 ≈ 1 token
            estimated_tokens = len(content)
            
            if current_tokens + estimated_tokens > max_tokens and selected_messages:
                break
            
            selected_messages.insert(0, msg)
            current_tokens += estimated_tokens
        
        return selected_messages
    
    async def add_memory_to_prompt(
        self,
        session_id: str,
        memory_id: Optional[str],
        base_prompt: str
    ) -> str:
        """
        将记忆添加到提示词中
        
        Args:
            session_id: 会话ID
            memory_id: 记忆配置ID
            base_prompt: 基础提示词
            
        Returns:
            str: 增强后的提示词
        """
        if not memory_id:
            return base_prompt
        
        # 获取记忆配置
        config = await self.get_memory_config(memory_id)
        if not config:
            return base_prompt
        
        # 获取格式化的历史
        history = await self.get_formatted_history(
            session_id,
            memory_type=config.memory_type,
            memory_params=config.memory_params
        )
        
        if not history:
            return base_prompt
        
        # 将历史添加到提示词
        enhanced_prompt = f"""{base_prompt}

=== 历史对话上下文 ===
{history}
=== 历史对话结束 ===

请基于以上历史对话上下文回答用户的新问题。"""
        
        return enhanced_prompt
