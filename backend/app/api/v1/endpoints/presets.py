"""
预设方案 API

提供预设方案的CRUD接口
支持原子化查询五大资源池信息
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import (
    KnowledgeBase,
    MemoryConfig,
    ModelConfig,
    PluginConfig,
    Preset,
    PromptConfig,
)
from app.schemas import (
    KnowledgeBaseInfo,
    MemoryInfo,
    ModelInfo,
    PluginInfo,
    PresetCloneRequest,
    PresetCreate,
    PresetDetail,
    PresetInDB,
    PresetList,
    PresetUpdate,
    PromptInfo,
    ResponseBase,
)

router = APIRouter()


@router.get("", response_model=ResponseBase[List[PresetList]])
async def list_presets(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取预设方案列表（包含资源名称摘要）"""
    result = await db.execute(
        select(Preset).offset(skip).limit(limit)
    )
    presets = result.scalars().all()
    
    # 批量查询所有资源信息用于组装列表数据
    preset_list_items = []
    for p in presets:
        # 查询模型名称
        # 现在selected_model存储的是具体模型名称，直接使用即可
        model_name = p.selected_model if p.selected_model else None
        
        # 查询提示词名称
        prompt_name = None
        if p.selected_prompt:
            prompt_result = await db.execute(
                select(PromptConfig.prompt_name).where(PromptConfig.prompt_id == p.selected_prompt)
            )
            prompt_name = prompt_result.scalar_one_or_none()
        
        # 查询记忆配置名称
        memory_name = None
        if p.selected_memory:
            memory_result = await db.execute(
                select(MemoryConfig.memory_name).where(MemoryConfig.memory_id == p.selected_memory)
            )
            memory_name = memory_result.scalar_one_or_none()
        
        # 查询知识库名称列表
        knowledge_base_names = []
        if p.selected_knowledge_bases:
            for kb_id in p.selected_knowledge_bases:
                kb_result = await db.execute(
                    select(KnowledgeBase.kb_name).where(KnowledgeBase.kb_id == kb_id)
                )
                kb_name = kb_result.scalar_one_or_none()
                if kb_name:
                    knowledge_base_names.append(kb_name)
        
        # 查询插件名称列表
        plugin_names = []
        if p.selected_plugins:
            for plugin_id in p.selected_plugins:
                plugin_result = await db.execute(
                    select(PluginConfig.plugin_name).where(PluginConfig.plugin_id == plugin_id)
                )
                plugin_name = plugin_result.scalar_one_or_none()
                if plugin_name:
                    plugin_names.append(plugin_name)
        
        preset_list_items.append(PresetList(
            preset_id=p.preset_id,
            preset_name=p.preset_name,
            description=p.description,
            selected_model=p.selected_model,
            selected_prompt=p.selected_prompt,
            selected_memory=p.selected_memory,
            selected_plugins=p.selected_plugins or [],
            selected_knowledge_bases=p.selected_knowledge_bases or [],
            is_default=p.is_default,
            is_active=p.is_active,
            # 资源名称摘要
            model_name=model_name or p.selected_model,
            prompt_name=prompt_name,
            memory_name=memory_name,
            knowledge_base_names=knowledge_base_names,
            plugin_names=plugin_names,
        ))
    
    return ResponseBase(data=preset_list_items)


@router.get("/{preset_id}", response_model=ResponseBase[PresetDetail])
async def get_preset(
    preset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取预设方案详情（原子化查询五大资源池）"""
    # 1. 获取Preset基础信息
    result = await db.execute(
        select(Preset).where(Preset.preset_id == preset_id)
    )
    preset = result.scalar_one_or_none()
    
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    # 2. 原子化查询模型信息
    model_info = None
    if preset.selected_model:
        # 现在selected_model存储的是具体模型名称（如"glm-4"），需要在ModelConfig.model_name数组中查找
        # 使用contains方法检查JSON数组是否包含指定值
        model_result = await db.execute(
            select(ModelConfig).where(ModelConfig.model_name.contains([preset.selected_model]))
        )
        model = model_result.scalar_one_or_none()
        if model:
            model_info = ModelInfo(
                model_id=model.model_id,
                model_name=model.model_name,
                model_type=model.model_type,
                provider=model.provider,
                api_base=model.api_base,
            )
    
    # 3. 原子化查询提示词/人格信息
    prompt_info = None
    if preset.selected_prompt:
        prompt_result = await db.execute(
            select(PromptConfig).where(PromptConfig.prompt_id == preset.selected_prompt)
        )
        prompt = prompt_result.scalar_one_or_none()
        if prompt:
            prompt_info = PromptInfo(
                prompt_id=prompt.prompt_id,
                prompt_name=prompt.prompt_name,
                system_prompt=prompt.system_prompt,
                variables=prompt.variables or [],
                temperature_override=prompt.temperature_override,
            )
    
    # 4. 原子化查询记忆配置信息
    memory_info = None
    if preset.selected_memory:
        memory_result = await db.execute(
            select(MemoryConfig).where(MemoryConfig.memory_id == preset.selected_memory)
        )
        memory = memory_result.scalar_one_or_none()
        if memory:
            memory_info = MemoryInfo(
                memory_id=memory.memory_id,
                memory_name=memory.memory_name,
                memory_type=memory.memory_type,
                memory_params=memory.memory_params or {},
            )
    
    # 5. 原子化查询知识库信息列表
    knowledge_bases_info = []
    if preset.selected_knowledge_bases:
        for kb_id in preset.selected_knowledge_bases:
            kb_result = await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.kb_id == kb_id)
            )
            kb = kb_result.scalar_one_or_none()
            if kb:
                knowledge_bases_info.append(KnowledgeBaseInfo(
                    kb_id=kb.kb_id,
                    kb_name=kb.kb_name,
                    description=kb.description,
                    embedding_model=kb.embedding_model,
                    document_count=kb.document_count,
                    total_chunks=kb.total_chunks,
                ))
    
    # 6. 原子化查询插件信息列表
    plugins_info = []
    if preset.selected_plugins:
        for plugin_id in preset.selected_plugins:
            plugin_result = await db.execute(
                select(PluginConfig).where(PluginConfig.plugin_id == plugin_id)
            )
            plugin = plugin_result.scalar_one_or_none()
            if plugin:
                plugins_info.append(PluginInfo(
                    plugin_id=plugin.plugin_id,
                    plugin_name=plugin.plugin_name,
                    class_name=plugin.class_name,
                    module_path=plugin.module_path,
                ))
    
    # 7. 组装完整的Preset详情
    preset_data = PresetDetail.model_validate(preset)
    preset_data.model_info = model_info
    preset_data.prompt_info = prompt_info
    preset_data.memory_info = memory_info
    preset_data.knowledge_bases_info = knowledge_bases_info
    preset_data.plugins_info = plugins_info
    
    return ResponseBase(data=preset_data)


@router.post("", response_model=ResponseBase[PresetInDB])
async def create_preset(
    preset: PresetCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建预设方案"""
    # 检查ID是否已存在
    result = await db.execute(
        select(Preset).where(Preset.preset_id == preset.preset_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Preset ID already exists")
    
    db_preset = Preset(**preset.model_dump())
    db.add(db_preset)
    await db.commit()
    await db.refresh(db_preset)
    
    return ResponseBase(data=PresetInDB.model_validate(db_preset))


@router.put("/{preset_id}", response_model=ResponseBase[PresetInDB])
async def update_preset(
    preset_id: str,
    preset_update: PresetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新预设方案"""
    result = await db.execute(
        select(Preset).where(Preset.preset_id == preset_id)
    )
    db_preset = result.scalar_one_or_none()
    
    if not db_preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    # 更新字段
    update_data = preset_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_preset, field, value)
    
    await db.commit()
    await db.refresh(db_preset)
    
    return ResponseBase(data=PresetInDB.model_validate(db_preset))


@router.delete("/{preset_id}")
async def delete_preset(
    preset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除预设方案"""
    result = await db.execute(
        select(Preset).where(Preset.preset_id == preset_id)
    )
    db_preset = result.scalar_one_or_none()
    
    if not db_preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    await db.delete(db_preset)
    await db.commit()
    
    return ResponseBase(message="Preset deleted successfully")


@router.post("/{preset_id}/clone", response_model=ResponseBase[PresetInDB])
async def clone_preset(
    preset_id: str,
    clone_request: PresetCloneRequest,
    db: AsyncSession = Depends(get_db)
):
    """克隆预设方案"""
    # 获取源预设
    result = await db.execute(
        select(Preset).where(Preset.preset_id == preset_id)
    )
    source_preset = result.scalar_one_or_none()
    
    if not source_preset:
        raise HTTPException(status_code=404, detail="Source preset not found")
    
    # 检查新ID是否已存在
    result = await db.execute(
        select(Preset).where(Preset.preset_id == clone_request.new_preset_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="New preset ID already exists")
    
    # 创建副本
    preset_data = source_preset.to_dict()
    preset_data.pop("id")
    preset_data.pop("created_at")
    preset_data.pop("updated_at")
    preset_data["preset_id"] = clone_request.new_preset_id
    preset_data["preset_name"] = clone_request.new_preset_name or f"{source_preset.preset_name} (Copy)"
    preset_data["is_default"] = False
    
    new_preset = Preset(**preset_data)
    db.add(new_preset)
    await db.commit()
    await db.refresh(new_preset)
    
    return ResponseBase(data=PresetInDB.model_validate(new_preset))
