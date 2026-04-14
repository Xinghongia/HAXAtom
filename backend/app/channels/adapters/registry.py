"""
渠道注册表

提供全局渠道管理功能
"""

from typing import Dict

from app.channels.adapters.base import (
    ChannelAdapter,
    ChannelRegistry,
    channel_registry,
)


def get_adapter(channel_type: str) -> ChannelAdapter:
    """
    获取指定类型的渠道适配器

    Args:
        channel_type: 渠道类型 (qq, feishu, dingtalk, telegram, web)

    Returns:
        ChannelAdapter: 渠道适配器实例

    Raises:
        ValueError: 不支持的渠道类型
    """
    adapter = channel_registry.get_adapter(channel_type)
    if not adapter:
        raise ValueError(f"Unsupported channel type: {channel_type}")
    return adapter


def list_supported_channels() -> list:
    """
    获取所有支持的渠道类型

    Returns:
        list: 渠道类型列表
    """
    return channel_registry.get_supported_channels()


__all__ = [
    "ChannelAdapter",
    "ChannelRegistry",
    "channel_registry",
    "get_adapter",
    "list_supported_channels",
]
