"""
预设方案 Schema

Preset 的 Pydantic 模型定义
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import TimestampMixin


# ==================== 资源池信息 Schema（用于Preset详情展示）====================

class ModelInfo(BaseModel):
    """模型资源信息"""
    model_id: str
    model_name: List[str]
    model_type: str
    provider: str
    api_base: Optional[str] = None


class PromptInfo(BaseModel):
    """提示词/人格资源信息"""
    prompt_id: str
    prompt_name: str
    system_prompt: str
    variables: Optional[List[str]] = []
    temperature_override: Optional[float] = None


class MemoryInfo(BaseModel):
    """记忆资源配置信息"""
    memory_id: str
    memory_name: str
    memory_type: str
    memory_params: Optional[Dict[str, Any]] = {}


class KnowledgeBaseInfo(BaseModel):
    """知识库资源信息"""
    kb_id: str
    kb_name: str
    description: Optional[str] = None
    embedding_model: str
    document_count: int
    total_chunks: int


class PluginInfo(BaseModel):
    """插件资源信息"""
    plugin_id: str
    plugin_name: str
    class_name: str
    module_path: Optional[str] = None


class ChannelConfig(BaseModel):
    """渠道配置"""
    enable_web: bool = Field(default=True)
    enable_feishu: bool = Field(default=False)
    enable_dingtalk: bool = Field(default=False)
    enable_telegram: bool = Field(default=False)


class OverrideConfig(BaseModel):
    """覆盖配置"""
    model_params: Optional[Dict[str, Any]] = Field(default=None)


class PresetBase(BaseModel):
    """预设方案基础字段"""
    preset_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    preset_name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(default=None)
    
    # 资源引用
    selected_model: str = Field(..., description="引用的具体模型名称（如'glm-4'），而不是ModelConfig的ID")
    selected_prompt: Optional[str] = Field(default=None, description="引用的提示词ID")
    selected_memory: Optional[str] = Field(default=None, description="引用的记忆ID")
    selected_plugins: Optional[List[str]] = Field(default_factory=list, description="引用的插件ID列表")
    selected_knowledge_bases: Optional[List[str]] = Field(
        default_factory=list, description="引用的知识库ID列表"
    )
    
    # 配置
    overrides: Optional[OverrideConfig] = Field(default=None)
    channel_config: Optional[ChannelConfig] = Field(default_factory=ChannelConfig)
    
    # 标记
    is_default: bool = Field(default=False)
    is_active: bool = Field(default=True)


class PresetCreate(PresetBase):
    """创建预设方案请求"""
    pass


class PresetUpdate(BaseModel):
    """更新预设方案请求"""
    preset_name: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = None
    selected_model: Optional[str] = None
    selected_prompt: Optional[str] = None
    selected_memory: Optional[str] = None
    selected_plugins: Optional[List[str]] = None
    selected_knowledge_bases: Optional[List[str]] = None
    overrides: Optional[OverrideConfig] = None
    channel_config: Optional[ChannelConfig] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class PresetInDB(PresetBase, TimestampMixin):
    """数据库中的预设方案"""
    id: int
    
    class Config:
        from_attributes = True


class PresetDetail(PresetInDB):
    """预设方案详情（包含原子化查询的完整资源信息）"""
    # 原子化资源信息 - 从五大资源池查询得到的完整信息
    model_info: Optional[ModelInfo] = Field(default=None, description="模型完整信息")
    prompt_info: Optional[PromptInfo] = Field(default=None, description="提示词/人格完整信息")
    memory_info: Optional[MemoryInfo] = Field(default=None, description="记忆配置完整信息")
    knowledge_bases_info: Optional[List[KnowledgeBaseInfo]] = Field(default_factory=list, description="知识库完整信息列表")
    plugins_info: Optional[List[PluginInfo]] = Field(default_factory=list, description="插件完整信息列表")


class PresetList(BaseModel):
    """预设方案列表项（包含资源名称摘要）"""
    preset_id: str
    preset_name: str
    description: Optional[str]
    selected_model: str
    selected_prompt: Optional[str]
    selected_memory: Optional[str]
    selected_plugins: Optional[List[str]]
    selected_knowledge_bases: Optional[List[str]]
    is_default: bool
    is_active: bool
    # 资源名称摘要（用于列表展示）
    model_name: Optional[str] = Field(default=None, description="模型名称")
    prompt_name: Optional[str] = Field(default=None, description="提示词/人格名称")
    memory_name: Optional[str] = Field(default=None, description="记忆配置名称")
    knowledge_base_names: Optional[List[str]] = Field(default_factory=list, description="知识库名称列表")
    plugin_names: Optional[List[str]] = Field(default_factory=list, description="插件名称列表")
    
    class Config:
        from_attributes = True


class PresetCloneRequest(BaseModel):
    """克隆预设方案请求"""
    new_preset_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    new_preset_name: Optional[str] = Field(default=None, max_length=128)
