"""
HAXAtom FastAPI 主应用

应用入口，负责：
1. FastAPI 应用实例创建
2. 生命周期管理（启动/关闭）
3. 路由注册
4. 中间件配置
5. 异常处理
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import close_db, init_db
from app.db.init_data import init_default_data


def setup_logging():
    """配置日志系统"""
    # 创建日志目录（使用配置的 log_file 的父目录）
    log_dir = os.path.dirname(settings.log_file)
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # 控制台输出
            logging.StreamHandler(sys.stdout),
            # 文件输出
            logging.FileHandler(
                settings.log_file,
                encoding="utf-8"
            )
        ]
    )
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


# 初始化日志
setup_logging()
logger = logging.getLogger(__name__)

# 设置Windows控制台UTF-8编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时：
    1. 创建数据目录
    2. 初始化数据库
    3. 配置LangSmith（如启用）
    
    关闭时：
    1. 关闭数据库连接
    2. 清理资源
    """
    # 启动
    logger.info("[START] Starting HAXAtom...")
    
    try:
        # 创建数据目录（使用配置的绝对路径）
        db_dir = os.path.dirname(settings.database_url.replace("sqlite+aiosqlite:///", ""))
        os.makedirs(db_dir, exist_ok=True)
        
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        os.makedirs("data/uploads", exist_ok=True)
        
        # 日志目录已在 setup_logging() 中创建
        logger.info("[INIT] Data directories created")
        
        # 初始化数据库
        await init_db()
        logger.info("[DB] Database initialized")
        
        # 初始化默认数据
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await init_default_data(session)
        logger.info("[DB] Default data initialized")
        
        # 配置LangSmith
        if settings.langsmith_tracing:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key or ""
            os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
            logger.info(f"[LangSmith] Tracing enabled: {settings.langsmith_project}")

        # 启动所有已激活的机器人
        from app.channels.service import channel_service
        from app.models import Bot
        from sqlalchemy import select
        async with AsyncSessionLocal() as bot_session:
            result = await bot_session.execute(
                select(Bot).where(Bot.is_active == True)
            )
            active_bots = result.scalars().all()
            for bot in active_bots:
                try:
                    await channel_service.start_bot(bot.bot_id)
                    logger.info(f"[BOT] Started: {bot.bot_id}")
                except Exception as bot_err:
                    logger.warning(f"[BOT] Failed to start {bot.bot_id}: {bot_err}")

        logger.info("[OK] HAXAtom started successfully!")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to start HAXAtom: {e}", exc_info=True)
        raise
    
    yield
    
    # 关闭
    logger.info("[STOP] Shutting down HAXAtom...")
    try:
        # 停止所有机器人
        from app.channels.service import channel_service
        from app.models import Bot
        from sqlalchemy import select
        async with AsyncSessionLocal() as bot_session:
            result = await bot_session.execute(
                select(Bot).where(Bot.is_active == True)
            )
            active_bots = result.scalars().all()
            for bot in active_bots:
                try:
                    await channel_service.stop_bot(bot.bot_id)
                    logger.info(f"[BOT] Stopped: {bot.bot_id}")
                except Exception as bot_err:
                    logger.warning(f"[BOT] Failed to stop {bot.bot_id}: {bot_err}")

        await close_db()
        logger.info("[OK] Database connection closed")
    except Exception as e:
        logger.error(f"[ERROR] Error during shutdown: {e}", exc_info=True)


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="HAXAtom - AI Agent Management Platform",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",      # 始终启用 Swagger UI
    redoc_url="/redoc",    # 始终启用 ReDoc
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    # 记录错误日志
    logger.error(
        f"[ERROR] Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "request_url": str(request.url),
            "request_method": request.method,
            "client_host": request.client.host if request.client else None
        }
    )
    
    # 根据异常类型返回不同的错误信息
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": "Bad request",
                "detail": str(exc)
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "detail": str(exc) if settings.debug else "Please contact administrator"
        }
    )


# 健康检查
@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


# 根路由
@app.get("/", tags=["Root"])
async def root():
    """根路由"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# 注册API路由
from app.api.v1 import api_router
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
