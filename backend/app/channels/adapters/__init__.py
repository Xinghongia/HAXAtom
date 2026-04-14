"""
渠道适配器模块
"""

from app.channels.adapters.base import (
    ChannelAdapter,
    ChannelMessage,
    ChannelResponse,
    ChannelRegistry,
    ChannelType,
    MessageRole,
    channel_registry,
    register_adapter,
)

__all__ = [
    "ChannelAdapter",
    "ChannelMessage",
    "ChannelResponse",
    "ChannelRegistry",
    "ChannelType",
    "MessageRole",
    "channel_registry",
    "register_adapter",
]
