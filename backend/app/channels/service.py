"""
渠道消息处理服务

将渠道适配器与 PresetEngine 连接
处理消息路由、回复发送、对话历史保存
"""

import logging
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.adapters.base import ChannelMessage
from app.channels.adapters.onebot11 import OneBot11Adapter
from app.core.preset_engine import PresetEngine
from app.db import async_session_maker
from app.models import Bot
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class ChannelService:
    """
    渠道消息处理服务

    职责：
    1. 接收渠道消息
    2. 查询 Bot 配置找到对应预设
    3. 调用 PresetEngine 处理
    4. 将回复通过渠道适配器发送
    5. 保存对话历史
    """

    def __init__(self):
        self._adapters: Dict[str, OneBot11Adapter] = {}
        self._running_bots: Dict[str, bool] = {}

    async def handle_message(self, channel_message: ChannelMessage) -> str:
        """
        处理接收到的渠道消息

        Args:
            channel_message: 统一格式的渠道消息

        Returns:
            str: AI 回复内容
        """
        logger.info(f"[ChannelService] 收到消息: session_id={channel_message.session_id}, content={channel_message.content[:50]}...")

        async with async_session_maker() as db:
            try:
                # 1. 根据 session_id 找到 Bot 配置
                bot = await self._get_bot_by_session(db, channel_message.session_id)
                if not bot:
                    logger.warning(f"[ChannelService] 未找到 Bot 配置: session_id={channel_message.session_id}")
                    return "机器人未配置"

                if not bot.is_active:
                    logger.warning(f"[ChannelService] Bot 未启用: bot_id={bot.bot_id}")
                    return "机器人已禁用"

                # 2. 确保对话存在，不存在则创建
                conversation_service = ConversationService(db)
                conversation = await conversation_service.get_conversation(channel_message.session_id)
                if not conversation:
                    conversation = await conversation_service.create_conversation(
                        preset_id=bot.preset_id,
                        session_id=channel_message.session_id,
                        channel_type=channel_message.channel_type,
                        channel_id=channel_message.channel_id,
                    )
                    logger.info(f"[ChannelService] 创建新对话: session_id={channel_message.session_id}")

                # 3. 保存用户消息到对话历史
                await conversation_service.add_message(
                    session_id=channel_message.session_id,
                    role="user",
                    content=channel_message.content,
                    auto_generate_title=True,
                )

                # 3. 调用 PresetEngine 处理
                preset_engine = PresetEngine(db)
                replies = []
                async for chunk in preset_engine.chat(
                    preset_id=bot.preset_id,
                    message=channel_message.content,
                    session_id=channel_message.session_id,
                    stream=True,
                    enable_tools=True,
                    enable_rag=True,
                    enable_memory=True,
                ):
                    replies.append(chunk)

                full_reply = "".join(replies)

                # 4. 保存 AI 回复到对话历史
                await conversation_service.add_message(
                    session_id=channel_message.session_id,
                    role="assistant",
                    content=full_reply,
                )

                # 5. 发送回复到渠道
                adapter = self._adapters.get(channel_message.channel_type)
                if adapter:
                    await adapter.send_message(
                        user_id=channel_message.user_id,
                        group_id=channel_message.group_id,
                        message=full_reply,
                    )

                logger.info(f"[ChannelService] 回复已发送: {full_reply[:50]}...")
                return full_reply

            except Exception as e:
                logger.error(f"[ChannelService] 处理消息失败: {e}", exc_info=True)
                return f"处理失败: {str(e)}"

    async def _get_bot_by_session(self, db: AsyncSession, session_id: str) -> Optional[Bot]:
        """
        根据 session_id 查找 Bot 配置

        session_id 格式:
        - onebot11_private_{user_id}
        - onebot11_group_{group_id}_{user_id}
        """
        parts = session_id.split("_")
        if len(parts) < 2:
            return None

        channel_type = parts[0]
        if len(parts) == 3 and parts[1] == "private":
            # onebot11_private_{user_id}
            user_id = parts[2]
            # 这里需要通过其他方式查找，暂时返回所有该渠道类型的第一个
            result = await db.execute(
                select(Bot).where(Bot.channel_type == channel_type, Bot.is_active == True)
            )
            return result.scalar_one_or_none()

        elif len(parts) >= 4 and parts[1] == "group":
            # onebot11_group_{group_id}_{user_id}
            group_id = parts[2]
            result = await db.execute(
                select(Bot).where(Bot.channel_type == channel_type, Bot.is_active == True)
            )
            return result.scalar_one_or_none()

        return None

    async def start_bot(self, bot_id: str) -> bool:
        """
        启动指定的 Bot

        Args:
            bot_id: 机器人 ID

        Returns:
            bool: 是否启动成功
        """
        async with async_session_maker() as db:
            result = await db.execute(
                select(Bot).where(Bot.bot_id == bot_id, Bot.is_active == True)
            )
            bot = result.scalar_one_or_none()

            if not bot:
                logger.error(f"[ChannelService] Bot 不存在或未启用: {bot_id}")
                return False

            if bot.channel_type == "onebot11":
                adapter = self._adapters.get("onebot11")
                if not adapter:
                    adapter = OneBot11Adapter()
                    self._adapters["onebot11"] = adapter

                # 设置消息处理器
                adapter.set_message_handler(self.handle_message)

                # 加载配置
                await adapter.load_all_configs(db)

                # 从配置获取监听地址
                from app.models import OneBot11Config
                config_result = await db.execute(
                    select(OneBot11Config).where(OneBot11Config.bot_id == bot_id)
                )
                config = config_result.scalar_one_or_none()

                if config:
                    await adapter.start_server(
                        host=config.listen_host,
                        port=config.listen_port,
                        token=config.token,
                    )
                    self._running_bots[bot_id] = True
                    logger.info(f"[ChannelService] Bot 已启动: {bot_id}")
                    return True
                else:
                    logger.error(f"[ChannelService] Bot 配置不存在: {bot_id}")
                    return False

            else:
                logger.warning(f"[ChannelService] 暂不支持的渠道类型: {bot.channel_type}")
                return False

    async def stop_bot(self, bot_id: str) -> bool:
        """
        停止指定的 Bot

        Args:
            bot_id: 机器人 ID

        Returns:
            bool: 是否停止成功
        """
        if bot_id in self._running_bots:
            adapter = self._adapters.get("onebot11")
            if adapter:
                await adapter.stop_server()
            self._running_bots.pop(bot_id, None)
            logger.info(f"[ChannelService] Bot 已停止: {bot_id}")
            return True
        return False


# 全局服务实例
channel_service = ChannelService()
