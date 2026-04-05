"""
对话服务

提供对话历史管理功能 - 支持多平台（Web、QQ、飞书等）
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation


class ConversationService:
    """
    对话服务
    
    管理对话历史的创建、查询、更新、删除
    支持多平台：Web、QQ、飞书、钉钉、Telegram等
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        初始化对话服务
        
        Args:
            db_session: 异步数据库会话
        """
        self.db = db_session
    
    # ==================== 会话ID生成器 ====================
    
    def _generate_web_session_id(self) -> str:
        """生成Web平台会话ID"""
        return f"web_{uuid.uuid4().hex[:12]}"
    
    def _generate_qq_session_id(self, user_id: str, group_id: Optional[str] = None) -> str:
        """
        生成QQ平台会话ID
        
        Args:
            user_id: QQ用户ID
            group_id: QQ群ID（群聊时传入）
            
        Returns:
            str: 会话ID
        """
        if group_id:
            return f"qq_group_{group_id}_{user_id}"
        return f"qq_private_{user_id}"
    
    def _generate_feishu_session_id(self, user_id: str) -> str:
        """生成飞书平台会话ID"""
        return f"feishu_{user_id}"
    
    def _generate_dingtalk_session_id(self, user_id: str) -> str:
        """生成钉钉平台会话ID"""
        return f"dingtalk_{user_id}"
    
    def _generate_telegram_session_id(self, chat_id: str, user_id: str) -> str:
        """生成Telegram平台会话ID"""
        return f"tg_{chat_id}_{user_id}"
    
    # ==================== 对话管理 ====================
    
    async def create_conversation(
        self,
        preset_id: str,
        title: Optional[str] = None,
        session_id: Optional[str] = None,
        channel_type: str = "web",
        channel_id: Optional[str] = None,
        platform_config: Optional[dict] = None
    ) -> Conversation:
        """
        创建新对话
        
        Args:
            preset_id: 预设方案ID
            title: 对话标题，为空则自动生成
            session_id: 会话ID，为空则自动生成
            channel_type: 平台类型，默认web
            channel_id: 平台特定ID（QQ号、飞书用户ID等）
            platform_config: 平台特定配置
            
        Returns:
            Conversation: 创建的对话对象
        """
        if not session_id:
            session_id = self._generate_web_session_id()
        
        if not title:
            title = "新对话"
        
        conversation = Conversation(
            session_id=session_id,
            channel_type=channel_type,
            channel_id=channel_id,
            preset_id=preset_id,
            title=title,
            messages=[],
            message_count=0,
            platform_config=platform_config
        )
        
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def get_or_create_conversation(
        self,
        preset_id: str,
        session_id: str,
        channel_type: str = "web",
        channel_id: Optional[str] = None,
        platform_config: Optional[dict] = None
    ) -> Conversation:
        """
        获取或创建对话
        
        如果会话ID已存在则返回现有对话，否则创建新对话
        
        Args:
            preset_id: 预设方案ID
            session_id: 会话ID
            channel_type: 平台类型
            channel_id: 平台特定ID
            platform_config: 平台特定配置
            
        Returns:
            Conversation: 对话对象
        """
        conversation = await self.get_conversation(session_id)
        
        if conversation:
            return conversation
        
        return await self.create_conversation(
            preset_id=preset_id,
            session_id=session_id,
            channel_type=channel_type,
            channel_id=channel_id,
            platform_config=platform_config
        )
    
    async def get_conversation(
        self,
        session_id: str
    ) -> Optional[Conversation]:
        """
        根据会话ID获取对话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Conversation]: 对话对象，不存在则返回None
        """
        result = await self.db.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_conversation_by_id(
        self,
        conversation_id: int
    ) -> Optional[Conversation]:
        """
        根据ID获取对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            Optional[Conversation]: 对话对象，不存在则返回None
        """
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()
    
    async def list_conversations(
        self,
        preset_id: Optional[str] = None,
        channel_type: Optional[str] = None,
        channel_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """
        获取对话列表
        
        Args:
            preset_id: 可选，按预设方案筛选
            channel_type: 可选，按平台类型筛选（web、qq、feishu等）
            channel_id: 可选，按平台ID筛选
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            List[Conversation]: 对话列表
        """
        query = select(Conversation)
        
        if preset_id:
            query = query.where(Conversation.preset_id == preset_id)
        
        if channel_type:
            query = query.where(Conversation.channel_type == channel_type)
        
        if channel_id:
            query = query.where(Conversation.channel_id == channel_id)
        
        query = query.order_by(desc(Conversation.updated_at))
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def list_conversations_by_platform(
        self,
        channel_type: str,
        channel_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """
        按平台获取对话列表
        
        Args:
            channel_type: 平台类型（web、qq、qq_group、qq_private、feishu、dingtalk、telegram）
            channel_id: 可选，按平台特定ID筛选
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            List[Conversation]: 对话列表
        """
        return await self.list_conversations(
            channel_type=channel_type,
            channel_id=channel_id,
            skip=skip,
            limit=limit
        )
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        auto_generate_title: bool = True
    ) -> Conversation:
        """
        添加消息到对话
        
        Args:
            session_id: 会话ID
            role: 消息角色 (user/assistant/system/tool)
            content: 消息内容
            auto_generate_title: 是否自动根据首条消息生成标题
            
        Returns:
            Conversation: 更新后的对话对象
            
        Raises:
            ValueError: 对话不存在
        """
        conversation = await self.get_conversation(session_id)
        
        if not conversation:
            raise ValueError(f"Conversation with session_id '{session_id}' not found")
        
        # 添加消息
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 确保 messages 是一个新的列表（避免 SQLAlchemy JSON 可变性问题）
        current_messages = list(conversation.messages) if conversation.messages else []
        current_messages.append(message)
        conversation.messages = current_messages
        conversation.message_count = len(conversation.messages)
        
        # 添加日志
        from app.main import logger
        logger.info(f"[ConversationService] 添加消息到 {session_id}: {role}, 当前共 {conversation.message_count} 条消息")
        
        # 自动根据首条用户消息生成标题
        if auto_generate_title and conversation.title == "新对话" and role == "user":
            conversation.title = self._generate_title(content)
        
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def update_title(
        self,
        session_id: str,
        title: str
    ) -> Conversation:
        """
        更新对话标题
        
        Args:
            session_id: 会话ID
            title: 新标题
            
        Returns:
            Conversation: 更新后的对话对象
            
        Raises:
            ValueError: 对话不存在
        """
        conversation = await self.get_conversation(session_id)
        
        if not conversation:
            raise ValueError(f"Conversation with session_id '{session_id}' not found")
        
        conversation.title = title
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def clear_messages(
        self,
        session_id: str
    ) -> Conversation:
        """
        清空对话消息（保留对话记录）
        
        Args:
            session_id: 会话ID
            
        Returns:
            Conversation: 更新后的对话对象
            
        Raises:
            ValueError: 对话不存在
        """
        conversation = await self.get_conversation(session_id)
        
        if not conversation:
            raise ValueError(f"Conversation with session_id '{session_id}' not found")
        
        conversation.messages = []
        conversation.message_count = 0
        
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def delete_conversation(
        self,
        session_id: str
    ) -> bool:
        """
        删除对话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功删除
        """
        conversation = await self.get_conversation(session_id)
        
        if not conversation:
            return False
        
        await self.db.delete(conversation)
        await self.db.commit()
        
        return True
    
    # ==================== 工具方法 ====================
    
    def _generate_title(self, first_message: str, max_length: int = 20) -> str:
        """
        根据首条消息生成标题
        
        Args:
            first_message: 首条消息内容
            max_length: 标题最大长度
            
        Returns:
            str: 生成的标题
        """
        # 去除首尾空白
        title = first_message.strip()
        
        # 截取前N个字符
        if len(title) > max_length:
            title = title[:max_length] + "..."
        
        # 如果为空，返回默认标题
        if not title:
            title = "新对话"
        
        return title
    
    def get_messages_for_langchain(
        self,
        conversation: Conversation,
        limit: Optional[int] = None
    ) -> List[dict]:
        """
        获取格式化为LangChain使用的消息列表
        
        Args:
            conversation: 对话对象
            limit: 限制返回的消息数量（最新的N条）
            
        Returns:
            List[dict]: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
        """
        if not conversation.messages:
            return []
        
        messages = conversation.messages
        
        # 只保留 user 和 assistant 消息
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
            if msg["role"] in ["user", "assistant"]
        ]
        
        # 限制数量
        if limit and len(messages) > limit:
            messages = messages[-limit:]
        
        return messages
