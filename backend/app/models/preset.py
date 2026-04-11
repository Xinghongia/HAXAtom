"""
预设方案表

存储预设方案的配置，引用五大资源池
"""

from typing import Optional, List

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Preset(Base):
    """
    预设方案表
    
    核心载体，从五大资源池中挑选原子化资源进行组合
    """
    
    __tablename__ = "presets"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    preset_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    preset_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 资源引用
    # selected_model: 存储具体模型名称（如"glm-4"），而不是ModelConfig的外键
    # 这样多个预设可以共享同一个模型提供商配置，但选择不同的具体模型
    selected_model: Mapped[str] = mapped_column(
        String(128), 
        nullable=False
    )
    selected_prompt: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("prompt_configs.prompt_id"),
        nullable=True
    )
    selected_memory: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("memory_configs.memory_id"),
        nullable=True
    )
    
    # JSON数组存储多选资源
    selected_plugins: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, default=list)
    selected_knowledge_bases: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True, default=list
    )
    
    # 覆盖配置和渠道配置
    overrides: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    channel_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # 标记
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 关系（可选，用于ORM关联查询）
    # 注意：selected_model现在存储的是具体模型名称，不再有外键关系
    prompt_config: Mapped[Optional["PromptConfig"]] = relationship("PromptConfig", lazy="selectin")
    memory_config: Mapped[Optional["MemoryConfig"]] = relationship("MemoryConfig", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Preset(preset_id='{self.preset_id}', model='{self.selected_model}')>"
