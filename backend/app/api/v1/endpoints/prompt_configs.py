"""
提示词配置 API

提供提示词配置的CRUD接口
"""

import re
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import PromptConfig
from app.schemas import (
    PromptConfigCreate,
    PromptConfigInDB,
    PromptConfigList,
    PromptConfigUpdate,
    ResponseBase,
)

router = APIRouter()


@router.get("", response_model=ResponseBase[List[PromptConfigList]])
async def list_prompts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取提示词配置列表"""
    result = await db.execute(
        select(PromptConfig).offset(skip).limit(limit)
    )
    prompts = result.scalars().all()
    
    return ResponseBase(data=[
        PromptConfigList(
            prompt_id=p.prompt_id,
            prompt_name=p.prompt_name,
            description=p.description,
            system_prompt=p.system_prompt,
            is_active=p.is_active,
            created_at=p.created_at
        ) for p in prompts
    ])


@router.get("/{prompt_id}", response_model=ResponseBase[PromptConfigInDB])
async def get_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取提示词配置详情"""
    result = await db.execute(
        select(PromptConfig).where(PromptConfig.prompt_id == prompt_id)
    )
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return ResponseBase(data=PromptConfigInDB.model_validate(prompt))


def generate_prompt_id(name: str) -> str:
    """根据名称生成prompt_id"""
    # 转换为小写，替换特殊字符为下划线
    prompt_id = re.sub(r'[^\w\s]', '', name.lower())
    prompt_id = re.sub(r'\s+', '_', prompt_id)
    prompt_id = prompt_id[:64]  # 限制长度
    # 添加随机后缀确保唯一性
    suffix = uuid.uuid4().hex[:8]
    return f"{prompt_id}_{suffix}"


@router.post("", response_model=ResponseBase[PromptConfigInDB])
async def create_prompt(
    prompt: PromptConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建提示词配置"""
    # 自动生成prompt_id
    prompt_id = generate_prompt_id(prompt.prompt_name)
    
    # 检查ID是否已存在（理论上不太可能，但还是检查一下）
    result = await db.execute(
        select(PromptConfig).where(PromptConfig.prompt_id == prompt_id)
    )
    if result.scalar_one_or_none():
        # 如果冲突，重新生成
        prompt_id = f"{prompt_id}_{uuid.uuid4().hex[:4]}"
    
    # 创建数据字典并添加prompt_id
    data = prompt.model_dump()
    data['prompt_id'] = prompt_id
    
    db_prompt = PromptConfig(**data)
    db.add(db_prompt)
    await db.commit()
    await db.refresh(db_prompt)
    
    return ResponseBase(data=PromptConfigInDB.model_validate(db_prompt))


@router.put("/{prompt_id}", response_model=ResponseBase[PromptConfigInDB])
async def update_prompt(
    prompt_id: str,
    prompt_update: PromptConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新提示词配置"""
    result = await db.execute(
        select(PromptConfig).where(PromptConfig.prompt_id == prompt_id)
    )
    db_prompt = result.scalar_one_or_none()
    
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # 更新字段
    update_data = prompt_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_prompt, field, value)
    
    await db.commit()
    await db.refresh(db_prompt)
    
    return ResponseBase(data=PromptConfigInDB.model_validate(db_prompt))


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除提示词配置"""
    result = await db.execute(
        select(PromptConfig).where(PromptConfig.prompt_id == prompt_id)
    )
    db_prompt = result.scalar_one_or_none()
    
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    await db.delete(db_prompt)
    await db.commit()
    
    return ResponseBase(message="Prompt deleted successfully")
