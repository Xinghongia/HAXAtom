"""
插件管理 API

提供插件的查询、启用/禁用、执行接口
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.plugins import PluginLoader, registry
from app.plugins.builtin.builtin_tools import BuiltinToolsPlugin
from app.schemas import ResponseBase

router = APIRouter()

# 初始化时加载内置插件
_builtin_plugins_loaded = False


def _ensure_builtin_plugins():
    """确保内置插件已加载"""
    global _builtin_plugins_loaded
    if not _builtin_plugins_loaded:
        registry.register(BuiltinToolsPlugin)
        _builtin_plugins_loaded = True


class PluginInfo(BaseModel):
    """插件信息"""
    id: str
    name: str
    description: str
    version: str
    author: str
    category: str
    icon: Optional[str]
    tags: List[str]
    source: str
    enabled: bool


class PluginExecuteRequest(BaseModel):
    """插件执行请求"""
    params: Dict[str, Any] = Field(default_factory=dict, description="执行参数")


class PluginExecuteResponse(BaseModel):
    """插件执行响应"""
    success: bool
    data: Any
    message: str
    error: Optional[str] = None


@router.get("", response_model=ResponseBase[List[PluginInfo]])
async def list_plugins(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有插件列表
    """
    _ensure_builtin_plugins()
    
    plugins = []
    for plugin_id in registry.list_plugins():
        metadata = registry.get_metadata(plugin_id)
        plugin = registry.get(plugin_id)
        if metadata and plugin:
            plugins.append(PluginInfo(
                id=plugin_id,
                name=metadata.name,
                description=metadata.description,
                version=metadata.version,
                author=metadata.author,
                category=metadata.category,
                icon=metadata.icon,
                tags=metadata.tags,
                source=metadata.source,
                enabled=plugin.enabled
            ))
    
    return ResponseBase(data=plugins)


@router.get("/{plugin_id}", response_model=ResponseBase[PluginInfo])
async def get_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取插件详情
    """
    _ensure_builtin_plugins()
    
    metadata = registry.get_metadata(plugin_id)
    plugin = registry.get(plugin_id)
    
    if not metadata or not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return ResponseBase(data=PluginInfo(
        id=plugin_id,
        name=metadata.name,
        description=metadata.description,
        version=metadata.version,
        author=metadata.author,
        category=metadata.category,
        icon=metadata.icon,
        tags=metadata.tags,
        source=metadata.source,
        enabled=plugin.enabled
    ))


@router.post("/{plugin_id}/execute", response_model=ResponseBase[PluginExecuteResponse])
async def execute_plugin(
    plugin_id: str,
    request: PluginExecuteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    执行插件

    示例参数：
    - time: {"tool": "time"}
    - search: {"tool": "search", "query": "Python"}
    """
    _ensure_builtin_plugins()
    
    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    if not plugin.enabled:
        raise HTTPException(status_code=400, detail="Plugin is disabled")
    
    # 验证参数
    valid, error = plugin.validate_params(request.params)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    # 执行插件
    result = await plugin.execute(request.params)
    
    return ResponseBase(data=PluginExecuteResponse(
        success=result.success,
        data=result.data,
        message=result.message,
        error=result.error
    ))


@router.post("/{plugin_id}/enable", response_model=ResponseBase[dict])
async def enable_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    启用插件
    """
    _ensure_builtin_plugins()
    
    success = registry.enable(plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return ResponseBase(data={"enabled": True, "plugin_id": plugin_id})


@router.post("/{plugin_id}/disable", response_model=ResponseBase[dict])
async def disable_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    禁用插件
    """
    _ensure_builtin_plugins()
    
    success = registry.disable(plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return ResponseBase(data={"enabled": False, "plugin_id": plugin_id})


@router.post("/reload", response_model=ResponseBase[dict])
async def reload_plugins(
    db: AsyncSession = Depends(get_db)
):
    """
    重新加载所有插件（开发调试用）
    """
    loader = PluginLoader(registry)
    loaded = loader.load_builtin_plugins()
    
    return ResponseBase(data={
        "reloaded": True,
        "loaded_plugins": loaded,
        "total": len(registry.list_plugins())
    })
