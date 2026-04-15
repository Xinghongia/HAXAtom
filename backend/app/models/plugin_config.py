"""
插件配置表

存储工具插件的独立配置
"""

from typing import Optional

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PluginConfig(Base):
    """
    插件配置表

    存储所有工具插件的独立配置
    """

    __tablename__ = "plugin_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plugin_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    plugin_name: Mapped[str] = mapped_column(String(128), nullable=False)
    class_name: Mapped[str] = mapped_column(String(128), nullable=False)
    module_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    plugin_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    config_schema: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 新增：来源分类
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="builtin")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    icon: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    author: Mapped[str] = mapped_column(String(128), nullable=False, default="Unknown")
    homepage: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    license: Mapped[str] = mapped_column(String(64), nullable=False, default="MIT")
    requirements: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    mcp_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    permission_level: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<PluginConfig(plugin_id='{self.plugin_id}', class_name='{self.class_name}')>"
