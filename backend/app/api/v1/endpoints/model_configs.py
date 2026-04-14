"""
模型配置 API

提供模型配置的 CRUD 接口
"""

from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import ModelConfig
from app.schemas import (
    ModelConfigCreate,
    ModelConfigInDB,
    ModelConfigList,
    ModelConfigResponse,
    ModelConfigUpdate,
    ResponseBase,
)

router = APIRouter()


# 各供应商的模型列表 API 端点
# 注意：不同供应商的模型列表 API 路径不同，这里使用各自的标准端点
PROVIDER_MODEL_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/models",
    "deepseek": "https://api.deepseek.com/v1/models",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4/models",  # 智谱 AI 标准端点
    "moonshot": "https://api.moonshot.cn/v1/models",
    "anthropic": "https://api.anthropic.com/v1/models",
    "aliyun_bailian": "https://dashscope.aliyuncs.com/compatible-mode/v1/models",
    "ollama": "http://localhost:11434/api/tags",  # Ollama 本地部署
}


def generate_zhipu_token(api_key: str) -> str:
    """
    生成智谱 AI 的 JWT Token
    智谱使用 JWT token 认证，需要自己生成
    
    API Key 格式：xxxx.yyyy
    - xxxx: API Key 的 ID 部分
    - yyyy: API Key 的 Secret 部分
    
    参考：https://open.bigmodel.cn/dev/api#howto
    智谱的 JWT 认证方式：
    - header: {"alg": "HS256", "sign_type": "SIGN"}
    - payload: {"api_key": "xxx", "exp": timestamp, "timestamp": timestamp}
    """
    try:
        from jose import jwt
        import time
        
        # API Key 格式为：xxxx.yyyy
        parts = api_key.split(".")
        if len(parts) != 2:
            print(f"API Key 格式不正确：{api_key}")
            return api_key  # 如果不是标准格式，直接返回原 key
        
        api_key_id = parts[0]
        api_key_secret = parts[1]
        
        # 当前时间戳（毫秒）
        timestamp = int(time.time() * 1000)
        
        # 构建 header - 智谱需要 sign_type: SIGN
        headers = {
            "alg": "HS256",
            "sign_type": "SIGN"
        }
        
        # 构建 payload
        # 智谱 AI 的 JWT payload 格式需要包含：api_key, exp, timestamp
        payload = {
            "api_key": api_key_id,
            "exp": timestamp + 3600 * 1000,  # 1 小时后过期（毫秒）
            "timestamp": timestamp
        }
        
        print(f"使用 api_key_id: {api_key_id}, secret: {api_key_secret[:4]}***")
        print(f"JWT payload: {payload}")
        
        # 生成 JWT token - 使用 api_key_secret 签名，带自定义 header
        token = jwt.encode(payload, api_key_secret, algorithm="HS256", headers=headers)
        print(f"智谱 token 生成成功：{token[:50]}...")
        return token
    except Exception as e:
        print(f"生成智谱 token 失败：{e}")
        import traceback
        traceback.print_exc()
        # 如果生成失败，返回原始 API Key
        return api_key


async def fetch_models_from_provider(
    provider: str, api_key: str, api_base: str = None
) -> List[Dict[str, Any]]:
    """
    从供应商获取模型列表
    
    Args:
        provider: 供应商名称
        api_key: API Key
        api_base: 自定义 API Base URL
        
    Returns:
        模型列表
    """
    # 获取默认端点
    default_endpoint = PROVIDER_MODEL_ENDPOINTS.get(provider)
    
    # 如果提供了 api_base，需要拼接 /models
    if api_base:
        # 去掉末尾的斜杠
        api_base = api_base.rstrip("/")
        
        # Ollama 特殊处理：使用 /api/tags 端点
        if provider == "ollama":
            endpoint = f"{api_base}/api/tags"
        else:
            endpoint = f"{api_base}/models"
    else:
        endpoint = default_endpoint
    
    if not endpoint:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # Ollama 不需要认证
    if provider == "ollama":
        headers = {}
    # Anthropic 使用不同的 header
    elif provider == "anthropic":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"请求模型列表：{endpoint}")
            if headers:
                print(f"Headers: Authorization: Bearer {api_key[:10]}***")
            
            response = await client.get(endpoint, headers=headers)
            print(f"响应状态码：{response.status_code}")
            print(f"响应内容：{response.text[:500]}")
            
            response.raise_for_status()
            data = response.json()
            
            # 不同供应商的响应格式不同
            if provider == "ollama":
                # Ollama 的响应格式：{"models": [...]}
                models = data.get("models", [])
                # 转换为统一格式
                return [
                    {
                        "id": model.get("name", ""),
                        "name": model.get("name", ""),
                        "size": model.get("size", 0),
                        "digest": model.get("digest", ""),
                        "modified_at": model.get("modified_at", ""),
                        "details": model.get("details", {}),
                    }
                    for model in models
                ]
            elif provider == "zhipu":
                # 智谱的响应格式
                return data.get("data", [])
            else:
                # OpenAI 兼容的格式（OpenAI, DeepSeek, Moonshot, Aliyun）
                return data.get("data", [])
                
    except httpx.HTTPError as e:
        print(f"HTTP 错误：{e}")
        if hasattr(e, "response"):
            print(f"响应内容：{e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code if hasattr(e, "response") else 500,
            detail=f"Failed to fetch models from {provider}: {str(e)}"
        )
    except Exception as e:
        print(f"其他错误：{e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching models: {str(e)}"
        )


@router.get("/providers/{provider}/models")
async def get_provider_models(
    provider: str,
    model_config_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定供应商的模型列表
    
    Args:
        provider: 供应商名称
        model_config_id: 可选的模型配置 ID，如果提供则使用该配置的 API Key
    """
    # 如果提供了 model_config_id，从数据库获取 API Key
    api_key = None
    api_base = None
    
    if model_config_id:
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.model_id == model_config_id)
        )
        model_config = result.scalar_one_or_none()
        
        if not model_config:
            raise HTTPException(status_code=404, detail="Model config not found")
        
        api_key = model_config.api_key
        api_base = model_config.api_base
    
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is required")
    
    # 智谱 AI 特殊处理：检查 API Key 格式
    if provider == "zhipu" and "." not in api_key:
        raise HTTPException(
            status_code=400,
            detail="智谱 AI 的 API Key 格式应为：xxxx.yyyy（由点号分隔的两部分）。请在智谱开放平台 (https://open.bigmodel.cn/) 获取正确的 API Key"
        )
    
    models = await fetch_models_from_provider(provider, api_key, api_base)
    
    # 格式化返回结果
    formatted_models = []
    for model in models:
        formatted_models.append({
            "id": model.get("id", ""),
            "name": model.get("name", model.get("id", "")),
            "object": model.get("object", "model"),
            "created": model.get("created", 0),
            "owned_by": model.get("owned_by", provider),
        })
    
    return ResponseBase(data=formatted_models)


@router.get("", response_model=ResponseBase[List[ModelConfigList]])
async def list_models(
    skip: int = 0,
    limit: int = 100,
    model_type: str = None,
    db: AsyncSession = Depends(get_db)
):
    """获取模型配置列表"""
    query = select(ModelConfig)
    
    if model_type:
        query = query.where(ModelConfig.model_type == model_type)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    return ResponseBase(data=[
        ModelConfigList(
            id=m.id,
            model_id=m.model_id,
            model_name=m.model_name,
            model_type=m.model_type,
            provider=m.provider,
            api_base=m.api_base,
            api_key=m.api_key,
            is_active=m.is_active,
            disabled_models=m.disabled_models or []
        ) for m in models
    ])


@router.get("/{model_id}", response_model=ResponseBase[ModelConfigResponse])
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取模型配置详情"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.model_id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return ResponseBase(data=ModelConfigResponse.model_validate(model))


@router.post("", response_model=ResponseBase[ModelConfigInDB])
async def create_model(
    model: ModelConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建模型配置"""
    # 检查ID是否已存在
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.model_id == model.model_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Model ID already exists")
    
    db_model = ModelConfig(**model.model_dump())
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    
    return ResponseBase(data=ModelConfigInDB.model_validate(db_model))


@router.put("/{model_id}", response_model=ResponseBase[ModelConfigInDB])
async def update_model(
    model_id: str,
    model_update: ModelConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新模型配置"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.model_id == model_id)
    )
    db_model = result.scalar_one_or_none()
    
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # 更新字段
    update_data = model_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_model, field, value)
    
    await db.commit()
    await db.refresh(db_model)
    
    return ResponseBase(data=ModelConfigInDB.model_validate(db_model))


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除模型配置"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.model_id == model_id)
    )
    db_model = result.scalar_one_or_none()
    
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    await db.delete(db_model)
    await db.commit()
    
    return ResponseBase(message="Model deleted successfully")
