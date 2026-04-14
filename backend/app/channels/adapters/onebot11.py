"""
OneBot v11 渠道适配器

基于 aiocqhttp 搭建反向 WebSocket 服务端
等待 NapCat 等客户端连接，通过 OneBot v11 协议通信
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from aiocqhttp import CQHttp, Event as AiocqhttpEvent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.adapters.base import ChannelAdapter, ChannelMessage
from app.core import PresetEngine
from app.db import get_db
from app.models import Bot, OneBot11Config

logger = logging.getLogger(__name__)


class OneBot11Adapter(ChannelAdapter):
    """
    OneBot v11 渠道适配器

    作为 WebSocket 服务端，等待 NapCat 等客户端连接
    """

    def __init__(self):
        self.bot: Optional[CQHttp] = None
        self._bots: Dict[str, Bot] = {}
        self._configs: Dict[str, OneBot11Config] = {}
        self._message_handler = None
        self._server_task: Optional[asyncio.Task] = None

    @property
    def channel_type(self) -> str:
        return "onebot11"

    def parse_message(self, raw_data: Dict[str, Any]) -> ChannelMessage:
        """
        解析 OneBot v11 消息为统一格式

        OneBot v11 消息格式:
        {
            "post_type": "message",
            "message_type": "private/group",
            "sub_type": "...",
            "user_id": 123456,
            "group_id": 987654,  # 仅群聊
            "message": [...],     # 消息段数组
            "raw_message": "...",
            "font": 0,
            "sender": {...},
            "time": 1234567890
        }
        """
        post_type = raw_data.get("post_type", "")
        message_type = raw_data.get("message_type", "")

        if post_type != "message":
            raise ValueError(f"Unsupported post_type: {post_type}")

        user_id = str(raw_data.get("user_id", ""))
        group_id = str(raw_data.get("group_id", "")) if raw_data.get("group_id") else None
        message_id = str(raw_data.get("message_id", ""))

        # 解析消息内容
        content = self._extract_message_content(raw_data.get("message", []))

        # 确定会话ID
        if message_type == "group":
            session_id = f"onebot11_group_{group_id}_{user_id}"
        else:
            session_id = f"onebot11_private_{user_id}"

        # 提取消息段用于工具调用
        raw_message = raw_data.get("raw_message", "")

        return ChannelMessage(
            session_id=session_id,
            channel_type="onebot11",
            user_id=user_id,
            content=content,
            role="user",
            message_id=message_id,
            channel_id=user_id,
            group_id=group_id,
            metadata={
                "message_type": message_type,
                "raw_message": raw_message,
                "sub_type": raw_data.get("sub_type", ""),
                "sender": raw_data.get("sender", {}),
            }
        )

    def _extract_message_content(self, message: Any) -> str:
        """
        从 OneBot v11 消息段中提取纯文本内容

        Args:
            message: 可能是字符串或消息段数组

        Returns:
            str: 纯文本消息内容
        """
        if isinstance(message, str):
            return message

        if isinstance(message, list):
            parts = []
            for seg in message:
                if isinstance(seg, dict):
                    if seg.get("type") == "text":
                        parts.append(seg.get("data", {}).get("text", ""))
                    elif seg.get("type") == "image":
                        parts.append("[图片]")
                    elif seg.get("type") == "at":
                        parts.append(f"@{seg.get('data', {}).get('qq', 'unknown')}")
                    elif seg.get("type") == "record":
                        parts.append("[语音]")
                    elif seg.get("type") == "video":
                        parts.append("[视频]")
                    else:
                        parts.append(f"[{seg.get('type')}]")
                elif isinstance(seg, str):
                    parts.append(seg)
            return "".join(parts)

        return str(message)

    def format_reply(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        将回复格式化为 OneBot v11 消息

        Returns:
            Dict: OneBot v11 格式的发送消息请求
        """
        return {"message": content}

    def set_message_handler(self, handler):
        """设置消息处理器"""
        self._message_handler = handler

    async def load_config(self, db: AsyncSession, bot_id: str) -> Optional[OneBot11Config]:
        """从数据库加载指定机器人的配置"""
        result = await db.execute(
            select(OneBot11Config).where(OneBot11Config.bot_id == bot_id)
        )
        return result.scalar_one_or_none()

    async def load_all_configs(self, db: AsyncSession):
        """加载所有 OneBot v11 机器人的配置"""
        result = await db.execute(select(OneBot11Config))
        configs = result.scalars().all()
        for config in configs:
            self._configs[config.bot_id] = config

        bot_result = await db.execute(select(Bot).where(Bot.channel_type == "onebot11"))
        bots = bot_result.scalars().all()
        for bot in bots:
            self._bots[bot.bot_id] = bot

    async def start_server(self, host: str = "0.0.0.0", port: int = 6199, token: str = None):
        """
        启动 OneBot v11 WebSocket 服务端

        Args:
            host: 监听地址
            port: 监听端口
            token: 鉴权 Token
        """
        self.bot = CQHttp(
            access_token=token,
            enable_http_post=False,
            enable_websocket_reverse=True,
        )

        @self.bot.on("message")
        async def handle_message(event: AiocqhttpEvent):
            """处理接收到的消息"""
            try:
                channel_msg = self.parse_message(event)
                logger.info(f"[OneBot11] 收到消息: {channel_msg.content}")

                if self._message_handler:
                    await self._message_handler(channel_msg)
                else:
                    logger.warning("[OneBot11] 未设置消息处理器")

            except Exception as e:
                logger.error(f"[OneBot11] 处理消息失败: {e}", exc_info=True)

            return None

        @self.bot.on("notice")
        async def handle_notice(event: AiocqhttpEvent):
            """处理通知事件"""
            logger.debug(f"[OneBot11] 收到通知: {event.dict()}")
            return None

        @self.bot.on("request")
        async def handle_request(event: AiocqhttpEvent):
            """处理请求事件"""
            logger.debug(f"[OneBot11] 收到请求: {event.dict()}")
            return None

        self._server_task = asyncio.create_task(self.bot.run_task(host=host, port=port))
        await asyncio.sleep(0.5)
        logger.info(f"[OneBot11] WebSocket 服务已启动 ws://{host}:{port}")

    async def stop_server(self):
        """停止服务器"""
        if self.bot:
            if self._server_task:
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass
                self._server_task = None
            await self.bot.close()
            self.bot = None
            logger.info("[OneBot11] WebSocket 服务已停止")

    async def send_message(self, user_id: str, group_id: Optional[str], message: str):
        """
        发送消息

        Args:
            user_id: 用户 ID（私聊用）
            group_id: 群 ID（群聊用）
            message: 消息内容
        """
        if not self.bot:
            raise RuntimeError("OneBot11 服务未启动")

        try:
            if group_id:
                # 群聊消息
                await self.bot.call_action('send_group_msg', group_id=int(group_id), message=message)
                logger.info(f"[OneBot11] 发送群消息到 {group_id}: {message}")
            else:
                # 私聊消息
                await self.bot.call_action('send_private_msg', user_id=int(user_id), message=message)
                logger.info(f"[OneBot11] 发送私聊消息到 {user_id}: {message}")
        except Exception as e:
            logger.error(f"[OneBot11] 发送消息失败: {e}", exc_info=True)


# 全局适配器实例
onebot11_adapter = OneBot11Adapter()
