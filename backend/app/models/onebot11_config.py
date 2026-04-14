"""
OneBot v11 渠道配置表

支持基于 OneBot v11 协议的机器人框架（如 NapCat、LLOneBot 等）
"""

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OneBot11Config(Base):
    """
    OneBot v11 渠道配置

    用于配置连接到我们 WebSocket 服务器的 OneBot v11 客户端
    支持 NapCat、LLOneBot 等兼容 OneBot v11 协议的实现
    """

    __tablename__ = "onebot11_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 关联 Bot
    bot_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("bots.bot_id"),
        nullable=False,
        unique=True,
        index=True
    )

    # OneBot v11 客户端连接配置（我们作为服务端）
    # 客户端配置：NapCat 等需要连接到这里配置的地址
    listen_host: Mapped[str] = mapped_column(
        String(128),
        default="0.0.0.0",
        comment="WebSocket 服务端监听地址"
    )
    listen_port: Mapped[int] = mapped_column(
        Integer,
        default=6199,
        comment="WebSocket 服务端监听端口"
    )
    token: Mapped[str] = mapped_column(
        String(256),
        nullable=True,
        comment="鉴权 Token（与客户端配置一致）"
    )

    # 消息格式
    message_post_format: Mapped[str] = mapped_column(
        String(16),
        default="array",
        comment="消息上报格式: array 或 string"
    )

    # 高级配置
    self_message: Mapped[bool] = mapped_column(
        JSON,
        default=False,
        comment="是否接收机器人自身消息"
    )
    extra_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment="额外配置"
    )

    # 状态
    is_active: Mapped[bool] = mapped_column(default=True)

    # 关系
    bot: Mapped["Bot"] = relationship("Bot", lazy="selectin")

    def __repr__(self) -> str:
        return f"<OneBot11Config(bot_id='{self.bot_id}', listen={self.listen_host}:{self.listen_port})>"
