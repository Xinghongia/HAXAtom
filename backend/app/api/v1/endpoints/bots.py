"""
机器人 API

提供机器人的 CRUD 接口
支持多渠道配置管理
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Bot, OneBot11Config, Preset
from app.schemas import (
    BotCreate,
    BotDetailResponse,
    BotResponse,
    BotUpdate,
    OneBot11ConfigCreate,
    OneBot11ConfigUpdate,
    ResponseBase,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=ResponseBase[List[BotResponse]])
async def list_bots(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取机器人列表"""
    result = await db.execute(
        select(Bot).offset(skip).limit(limit)
    )
    bots = result.scalars().all()

    return ResponseBase(data=[
        BotResponse(
            bot_id=b.bot_id,
            bot_name=b.bot_name,
            channel_type=b.channel_type,
            preset_id=b.preset_id,
            is_active=b.is_active,
        ) for b in bots
    ])


@router.get("/{bot_id}", response_model=ResponseBase[BotDetailResponse])
async def get_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取机器人详情（包含渠道配置）"""
    result = await db.execute(
        select(Bot).where(Bot.bot_id == bot_id)
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # 根据 channel_type 加载对应的渠道配置
    channel_config = None
    if bot.channel_type == "onebot11":
        config_result = await db.execute(
            select(OneBot11Config).where(OneBot11Config.bot_id == bot_id)
        )
        config = config_result.scalar_one_or_none()
        if config:
            channel_config = {
                "listen_host": config.listen_host,
                "listen_port": config.listen_port,
                "token": config.token,
                "message_post_format": config.message_post_format,
                "self_message": config.self_message,
                "is_active": config.is_active,
            }

    return ResponseBase(data=BotDetailResponse(
        bot_id=bot.bot_id,
        bot_name=bot.bot_name,
        channel_type=bot.channel_type,
        preset_id=bot.preset_id,
        is_active=bot.is_active,
        channel_config=channel_config,
    ))


@router.post("", response_model=ResponseBase[BotResponse])
async def create_bot(
    request: BotCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建机器人"""
    # 检查 bot_id 是否已存在
    existing = await db.execute(
        select(Bot).where(Bot.bot_id == request.bot_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bot ID already exists")

    # 检查 preset_id 是否存在
    preset_result = await db.execute(
        select(Preset).where(Preset.preset_id == request.preset_id)
    )
    if not preset_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Preset not found")

    # 创建 Bot
    bot = Bot(
        bot_id=request.bot_id,
        bot_name=request.bot_name,
        channel_type=request.channel_type,
        preset_id=request.preset_id,
        is_active=request.is_active,
    )
    db.add(bot)
    await db.commit()
    await db.refresh(bot)

    logger.info(f"[create_bot] 创建机器人: {bot.bot_id}")

    return ResponseBase(data=BotResponse(
        bot_id=bot.bot_id,
        bot_name=bot.bot_name,
        channel_type=bot.channel_type,
        preset_id=bot.preset_id,
        is_active=bot.is_active,
    ))


@router.put("/{bot_id}", response_model=ResponseBase[BotResponse])
async def update_bot(
    bot_id: str,
    request: BotUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新机器人"""
    result = await db.execute(
        select(Bot).where(Bot.bot_id == bot_id)
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # 更新字段
    if request.bot_name is not None:
        bot.bot_name = request.bot_name
    if request.preset_id is not None:
        # 检查 preset 是否存在
        preset_result = await db.execute(
            select(Preset).where(Preset.preset_id == request.preset_id)
        )
        if not preset_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Preset not found")
        bot.preset_id = request.preset_id
    if request.is_active is not None:
        bot.is_active = request.is_active

    await db.commit()
    await db.refresh(bot)

    logger.info(f"[update_bot] 更新机器人: {bot_id}")

    return ResponseBase(data=BotResponse(
        bot_id=bot.bot_id,
        bot_name=bot.bot_name,
        channel_type=bot.channel_type,
        preset_id=bot.preset_id,
        is_active=bot.is_active,
    ))


@router.delete("/{bot_id}", response_model=ResponseBase[dict])
async def delete_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除机器人"""
    result = await db.execute(
        select(Bot).where(Bot.bot_id == bot_id)
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # 删除关联的渠道配置
    if bot.channel_type == "onebot11":
        config_result = await db.execute(
            select(OneBot11Config).where(OneBot11Config.bot_id == bot_id)
        )
        config = config_result.scalar_one_or_none()
        if config:
            await db.delete(config)

    await db.delete(bot)
    await db.commit()

    logger.info(f"[delete_bot] 删除机器人: {bot_id}")

    return ResponseBase(data={"deleted": True, "bot_id": bot_id})


# ==================== OneBot v11 渠道配置接口 ====================

@router.post("/{bot_id}/onebot11-config", response_model=ResponseBase[dict])
async def create_onebot11_config(
    bot_id: str,
    request: OneBot11ConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建 OneBot v11 渠道配置"""
    # 检查 bot 是否存在
    bot_result = await db.execute(
        select(Bot).where(Bot.bot_id == bot_id)
    )
    bot = bot_result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if bot.channel_type != "onebot11":
        raise HTTPException(status_code=400, detail="Bot is not OneBot v11 type")

    # 检查是否已有配置
    existing = await db.execute(
        select(OneBot11Config).where(OneBot11Config.bot_id == bot_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="OneBot11 config already exists")

    config = OneBot11Config(
        bot_id=bot_id,
        listen_host=request.listen_host,
        listen_port=request.listen_port,
        token=request.token,
        message_post_format=request.message_post_format,
        self_message=request.self_message,
        extra_config=request.extra_config,
        is_active=True,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    logger.info(f"[create_onebot11_config] 为机器人 {bot_id} 创建 OneBot v11 配置")

    return ResponseBase(data={
        "bot_id": bot_id,
        "listen_host": config.listen_host,
        "listen_port": config.listen_port,
        "is_active": config.is_active,
    })


@router.put("/{bot_id}/onebot11-config", response_model=ResponseBase[dict])
async def update_onebot11_config(
    bot_id: str,
    request: OneBot11ConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新 OneBot v11 渠道配置"""
    result = await db.execute(
        select(OneBot11Config).where(OneBot11Config.bot_id == bot_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="OneBot11 config not found")

    # 更新字段
    if request.listen_host is not None:
        config.listen_host = request.listen_host
    if request.listen_port is not None:
        config.listen_port = request.listen_port
    if request.token is not None:
        config.token = request.token
    if request.message_post_format is not None:
        config.message_post_format = request.message_post_format
    if request.self_message is not None:
        config.self_message = request.self_message
    if request.extra_config is not None:
        config.extra_config = request.extra_config
    if request.is_active is not None:
        config.is_active = request.is_active

    await db.commit()
    await db.refresh(config)

    logger.info(f"[update_onebot11_config] 更新机器人 {bot_id} 的 OneBot v11 配置")

    return ResponseBase(data={
        "bot_id": bot_id,
        "listen_host": config.listen_host,
        "listen_port": config.listen_port,
        "is_active": config.is_active,
    })


@router.get("/{bot_id}/onebot11-config", response_model=ResponseBase[dict])
async def get_onebot11_config(
    bot_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取 OneBot v11 渠道配置"""
    result = await db.execute(
        select(OneBot11Config).where(OneBot11Config.bot_id == bot_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="OneBot11 config not found")

    return ResponseBase(data={
        "bot_id": config.bot_id,
        "listen_host": config.listen_host,
        "listen_port": config.listen_port,
        "token": config.token,
        "message_post_format": config.message_post_format,
        "self_message": config.self_message,
        "extra_config": config.extra_config,
        "is_active": config.is_active,
    })


@router.post("/{bot_id}/start", response_model=ResponseBase[dict])
async def start_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db)
):
    """启动机器人服务"""
    from app.channels.service import channel_service

    success = await channel_service.start_bot(bot_id)

    if success:
        return ResponseBase(data={"status": "started", "bot_id": bot_id})
    else:
        raise HTTPException(status_code=400, detail="启动失败，请检查配置")


@router.post("/{bot_id}/stop", response_model=ResponseBase[dict])
async def stop_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db)
):
    """停止机器人服务"""
    from app.channels.service import channel_service

    success = await channel_service.stop_bot(bot_id)

    if success:
        return ResponseBase(data={"status": "stopped", "bot_id": bot_id})
    else:
        raise HTTPException(status_code=400, detail="停止失败")
