"""
渠道适配器基类

定义统一的渠道接口，所有具体渠道适配器需继承 ChannelAdapter
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

BEIJING_TZ = timezone(timedelta(hours=8))


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChannelType(str, Enum):
    WEB = "web"
    QQ = "qq"
    QQ_GROUP = "qq_group"
    QQ_PRIVATE = "qq_private"
    FEISHU = "feishu"
    DINGTALK = "dingtalk"
    TELEGRAM = "telegram"


@dataclass
class ChannelMessage:
    """
    统一消息格式

    所有渠道的消息都会被转换成这个格式
    """
    session_id: str
    channel_type: str
    user_id: str
    content: str
    role: str = "user"
    message_id: Optional[str] = None
    channel_id: Optional[str] = None
    group_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(BEIJING_TZ).isoformat())

    def to_conversation_format(self) -> Dict[str, Any]:
        """转换为对话服务格式"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }


@dataclass
class ChannelResponse:
    """渠道响应格式"""
    content: str
    image_urls: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChannelAdapter(ABC):
    """
    渠道适配器基类

    所有具体渠道需实现以下方法：
    - parse_message: 解析原始消息
    - format_reply: 格式化回复消息
    - validate_signature: 验证签名（如果渠道需要）
    """

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """渠道类型标识"""
        pass

    @abstractmethod
    def parse_message(self, raw_data: Dict[str, Any]) -> ChannelMessage:
        """
        解析原始消息为统一格式

        Args:
            raw_data: 渠道原始消息数据

        Returns:
            ChannelMessage: 统一格式消息
        """
        pass

    @abstractmethod
    def format_reply(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        将统一回复格式转换为渠道特定格式

        Args:
            content: 回复内容
            **kwargs: 额外参数（如 image_urls 等）

        Returns:
            Dict: 渠道特定的响应格式
        """
        pass

    def validate_signature(self, raw_data: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """
        验证消息签名（可选实现）

        Args:
            raw_data: 原始消息数据
            headers: 请求头

        Returns:
            bool: 签名是否有效
        """
        return True

    def extract_user_info(self, raw_data: Dict[str, Any]) -> Dict[str, str]:
        """
        从消息中提取用户信息（可选实现）

        Args:
            raw_data: 原始消息数据

        Returns:
            Dict: 包含 user_id, group_id 等
        """
        return {}


class ChannelRegistry:
    """
    渠道注册表

    管理所有已注册的渠道适配器
    """

    def __init__(self):
        self._adapters: Dict[str, ChannelAdapter] = {}

    def register(self, adapter: ChannelAdapter) -> None:
        """注册渠道适配器"""
        self._adapters[adapter.channel_type] = adapter

    def get_adapter(self, channel_type: str) -> Optional[ChannelAdapter]:
        """获取渠道适配器"""
        return self._adapters.get(channel_type)

    def get_supported_channels(self) -> List[str]:
        """获取所有支持的渠道类型"""
        return list(self._adapters.keys())

    def unregister(self, channel_type: str) -> bool:
        """注销渠道适配器"""
        if channel_type in self._adapters:
            del self._adapters[channel_type]
            return True
        return False


# 全局注册表实例
channel_registry = ChannelRegistry()


def register_adapter(adapter_class: type) -> type:
    """
    渠道适配器注册装饰器

    用法:
        @register_adapter
        class MyAdapter(ChannelAdapter):
            ...
    """
    def wrapper(cls: type) -> type:
        adapter = cls()
        channel_registry.register(adapter)
        return cls
    return wrapper
