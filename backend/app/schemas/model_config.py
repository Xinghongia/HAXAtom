"""
模型配置 Schema

ModelConfig 的 Pydantic 模型定义
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import TimestampMixin


class ModelParams(BaseModel):
    """模型参数"""
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=0.9, ge=0, le=1)
    max_tokens: int = Field(default=4096, ge=1, le=8192)
    frequency_penalty: float = Field(default=0, ge=-2, le=2)
    presence_penalty: float = Field(default=0, ge=-2, le=2)


class ModelConfigBase(BaseModel):
    """模型配置基础字段"""
    model_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    model_name: List[str] = Field(..., min_length=1, description="模型名称列表，支持一个厂商配置多个模型如['glm-4', 'glm-5']")
    model_type: str = Field(default="chat", pattern=r"^(chat|embedding|tts|stt|rerank)$")
    provider: str = Field(..., pattern=r"^(openai|deepseek|ollama|anthropic|zhipu|moonshot|minimax|azure|gemini)$")
    api_base: Optional[str] = Field(default=None, max_length=256)
    default_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_active: bool = Field(default=True)
    disabled_models: Optional[List[str]] = Field(default=None, description="禁用的模型名称列表")


class ModelConfigCreate(ModelConfigBase):
    """创建模型配置请求"""
    api_key: Optional[str] = Field(default=None, description="API密钥，将被加密存储")


class ModelConfigUpdate(BaseModel):
    """更新模型配置请求"""
    model_name: Optional[List[str]] = Field(default=None, min_length=1)
    api_base: Optional[str] = Field(default=None, max_length=256)
    api_key: Optional[str] = Field(default=None)
    default_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    disabled_models: Optional[List[str]] = None


class ModelConfigInDB(ModelConfigBase, TimestampMixin):
    """数据库中的模型配置"""
    id: int
    api_key: Optional[str] = Field(default=None, description="API密钥")
    
    class Config:
        from_attributes = True


class ModelConfigResponse(ModelConfigInDB):
    """模型配置响应（API密钥做掩码处理）"""
    
    @field_validator("api_key", mode="before")
    @classmethod
    def mask_api_key(cls, v: Optional[str]) -> Optional[str]:
        """掩码API密钥"""
        if v:
            return "***SET***"
        return None


class ModelConfigList(BaseModel):
    """模型配置列表项（返回完整信息给前端）"""
    id: int
    model_id: str
    model_name: List[str]
    model_type: str
    provider: str
    api_base: Optional[str]
    api_key: Optional[str]
    is_active: bool
    disabled_models: Optional[List[str]] = Field(default_factory=list)
