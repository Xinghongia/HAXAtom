"""
机器人表

存储机器人实例配置，一个机器人 = 渠道路由 + 预设方案
"""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Bot(Base):
    """
    机器人表

    核心载体：
    - 渠道路由：通过 channel_type 关联具体渠道配置
    - 预设方案：通过 preset_id 引用预设方案
    """
    
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bot_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    bot_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # 渠道路由
    channel_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="渠道类型: onebot11, feishu, dingtalk, telegram, qqofficial"
    )

    # 关联预设方案
    preset_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("presets.preset_id"),
        nullable=False
    )

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    preset: Mapped["Preset"] = relationship("Preset", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Bot(bot_id='{self.bot_id}', channel='{self.channel_type}')>"
