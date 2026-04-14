"""
渠道模块

多IM渠道适配层 - 支持 QQ、飞书、钉钉、Telegram 等平台
"""

from app.channels.adapters.base import (
    ChannelAdapter,
    ChannelMessage,
    ChannelRegistry,
    register_adapter,
)
from app.channels.adapters.registry import channel_registry
from app.channels.service import ChannelService, channel_service
from app.channels.adapters.onebot11 import OneBot11Adapter, onebot11_adapter

__all__ = [
    "ChannelAdapter",
    "ChannelMessage",
    "ChannelRegistry",
    "channel_registry",
    "register_adapter",
    "ChannelService",
    "channel_service",
    "OneBot11Adapter",
    "onebot11_adapter",
]
