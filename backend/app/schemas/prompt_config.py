"""
提示词配置 Schema

PromptConfig 的 Pydantic 模型定义
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampMixin


class PresetDialogue(BaseModel):
    """预设对话项"""
    role: str = Field(..., description="角色: user 或 assistant")
    content: str = Field(..., description="对话内容")


class PromptConfigBase(BaseModel):
    """提示词配置基础字段"""
    prompt_name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, description="描述")
    system_prompt: str = Field(..., min_length=1)
    variables: Optional[List[str]] = Field(default_factory=list)
    temperature_override: Optional[float] = Field(default=None, ge=0, le=2)
    is_active: bool = Field(default=True)
    # 工具配置
    selected_tools: Optional[List[str]] = Field(default_factory=list, description="选中的工具ID列表")
    use_all_tools: bool = Field(default=True, description="是否使用全部工具")
    # 预设对话
    preset_dialogues: Optional[List[PresetDialogue]] = Field(default_factory=list, description="预设对话列表")


class PromptConfigCreate(PromptConfigBase):
    """创建提示词配置请求"""
    pass


class PromptConfigCreateResponse(PromptConfigBase):
    """创建提示词配置响应（包含自动生成的prompt_id）"""
    prompt_id: str


class PromptConfigUpdate(BaseModel):
    """更新提示词配置请求"""
    prompt_name: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = Field(default=None, description="描述")
    system_prompt: Optional[str] = None
    variables: Optional[List[str]] = None
    temperature_override: Optional[float] = Field(default=None, ge=0, le=2)
    is_active: Optional[bool] = None
    selected_tools: Optional[List[str]] = Field(default=None, description="选中的工具ID列表")
    use_all_tools: Optional[bool] = Field(default=None, description="是否使用全部工具")
    preset_dialogues: Optional[List[PresetDialogue]] = Field(default=None, description="预设对话列表")


class PromptConfigInDB(TimestampMixin):
    """数据库中的提示词配置"""
    id: int
    prompt_id: str
    prompt_name: str
    description: Optional[str] = Field(default=None, description="描述")
    system_prompt: str
    variables: Optional[List[str]] = Field(default_factory=list)
    temperature_override: Optional[float] = Field(default=None, ge=0, le=2)
    is_active: bool = Field(default=True)
    selected_tools: Optional[List[str]] = Field(default_factory=list, description="选中的工具ID列表")
    use_all_tools: bool = Field(default=True, description="是否使用全部工具")
    preset_dialogues: Optional[List[PresetDialogue]] = Field(default_factory=list, description="预设对话列表")
    
    class Config:
        from_attributes = True


class PromptConfigList(BaseModel):
    """提示词配置列表项"""
    prompt_id: str  # 用于删除等操作，前端可选择不展示
    prompt_name: str
    description: Optional[str] = Field(default=None, description="描述")
    system_prompt: str  # 系统提示词，卡片展示用
    is_active: bool
    created_at: datetime  # 创建时间
