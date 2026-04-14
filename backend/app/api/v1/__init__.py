"""
API V1 路由包

导出所有V1版本的路由
"""

from fastapi import APIRouter

from app.api.v1.endpoints import bots, chat, knowledge_base, memory_configs, model_configs, plugins, presets, prompt_configs, logs, system

api_router = APIRouter(prefix="/api/v1")

# 注册路由
api_router.include_router(model_configs.router, prefix="/models", tags=["模型配置"])
api_router.include_router(prompt_configs.router, prefix="/prompts", tags=["提示词配置"])
api_router.include_router(presets.router, prefix="/presets", tags=["预设方案"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["插件管理"])
api_router.include_router(knowledge_base.router, prefix="/knowledge-bases", tags=["知识库管理"])
api_router.include_router(memory_configs.router, prefix="/memories", tags=["记忆配置"])
api_router.include_router(chat.router, prefix="/chat", tags=["对话"])
api_router.include_router(logs.router, prefix="/logs", tags=["系统日志"])
api_router.include_router(system.router, prefix="/system", tags=["系统信息"])
api_router.include_router(bots.router, prefix="/bots", tags=["机器人管理"])

__all__ = ["api_router"]
