"""
Bot 机器人 Schema

Pydantic 模型定义
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class OneBot11ConfigSchema(BaseModel):
    """OneBot v11 渠道配置"""
    listen_host: str = Field(default="0.0.0.0", description="WebSocket 服务端监听地址")
    listen_port: int = Field(default=6199, description="WebSocket 服务端监听端口")
    token: Optional[str] = Field(default=None, description="鉴权 Token")
    message_post_format: Literal["array", "string"] = Field(default="array", description="消息上报格式")
    self_message: bool = Field(default=False, description="是否接收自身消息")
    extra_config: Optional[dict] = Field(default=None, description="额外配置")


class BotCreate(BaseModel):
    """创建机器人请求"""
    bot_id: str = Field(..., description="机器人唯一标识")
    bot_name: str = Field(..., description="机器人名称")
    channel_type: Literal["onebot11", "feishu", "dingtalk", "telegram", "qqofficial"] = Field(
        ..., description="渠道类型"
    )
    preset_id: str = Field(..., description="关联的预设方案 ID")
    is_active: bool = Field(default=True, description="是否启用")
    channel_config: Optional[dict] = Field(default=None, description="渠道特定配置（供将来扩展）")


class BotUpdate(BaseModel):
    """更新机器人请求"""
    bot_name: Optional[str] = Field(default=None, description="机器人名称")
    preset_id: Optional[str] = Field(default=None, description="关联的预设方案 ID")
    is_active: Optional[bool] = Field(default=None, description="是否启用")


class OneBot11ConfigCreate(BaseModel):
    """创建 OneBot v11 配置"""
    listen_host: str = Field(default="0.0.0.0", description="WebSocket 服务端监听地址")
    listen_port: int = Field(default=6199, description="WebSocket 服务端监听端口")
    token: Optional[str] = Field(default=None, description="鉴权 Token")
    message_post_format: Literal["array", "string"] = Field(default="array", description="消息上报格式")
    self_message: bool = Field(default=False, description="是否接收自身消息")
    extra_config: Optional[dict] = Field(default=None, description="额外配置")


class OneBot11ConfigUpdate(BaseModel):
    """更新 OneBot v11 配置"""
    listen_host: Optional[str] = Field(default=None, description="WebSocket 服务端监听地址")
    listen_port: Optional[int] = Field(default=None, description="WebSocket 服务端监听端口")
    token: Optional[str] = Field(default=None, description="鉴权 Token")
    message_post_format: Optional[Literal["array", "string"]] = Field(default=None, description="消息上报格式")
    self_message: Optional[bool] = Field(default=None, description="是否接收自身消息")
    extra_config: Optional[dict] = Field(default=None, description="额外配置")
    is_active: Optional[bool] = Field(default=None, description="是否启用")


class BotResponse(BaseModel):
    """机器人响应"""
    bot_id: str
    bot_name: str
    channel_type: str
    preset_id: str
    is_active: bool

    class Config:
        from_attributes = True


class BotDetailResponse(BotResponse):
    """机器人详情响应（包含渠道配置）"""
    channel_config: Optional[dict] = None

    class Config:
        from_attributes = True
