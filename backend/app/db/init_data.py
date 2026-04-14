"""
数据库初始化数据

包含默认模型配置、提示词模板和示例预设方案
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Bot, ModelConfig, OneBot11Config, PromptConfig, Preset, MemoryConfig
from app.db.session import AsyncSessionLocal


# 默认模型配置（只预设一个智谱可用模型）
DEFAULT_MODELS = [
    {
        "model_id": "zhipu_glm4",
        "model_name": ["glm-4", "glm-4-flash"],
        "model_type": "chat",
        "provider": "zhipu",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "api_key": "3941525c3e1c4e238f03bdd1805dcf57.kHaDKZvXNxL86ydw",
        "default_params": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 4096
        },
        "is_active": True
    }
]

# 默认记忆配置
DEFAULT_MEMORY_CONFIGS = [
    {
        "memory_id": "default_buffer",
        "memory_name": "默认滑动窗口记忆",
        "memory_type": "buffer_window",
        "memory_params": {
            "window_size": 10,
            "description": "保留最近10轮对话"
        },
        "is_active": True
    },
    {
        "memory_id": "long_buffer",
        "memory_name": "长对话记忆",
        "memory_type": "buffer_window",
        "memory_params": {
            "window_size": 50,
            "description": "保留最近50轮对话"
        },
        "is_active": True
    }
]

# 默认提示词/人格配置
DEFAULT_PROMPT_CONFIGS = [
    {
        "prompt_id": "default_assistant",
        "prompt_name": "默认助手",
        "description": "通用的AI助手角色",
        "system_prompt": "你是一个 helpful 的AI助手，能够回答用户的各种问题。",
        "variables": [],
        "temperature_override": 0.7,
        "is_active": True,
        "selected_tools": [],
        "use_all_tools": True,
        "preset_dialogues": []
    },
    {
        "prompt_id": "code_assistant",
        "prompt_name": "代码助手",
        "description": "专门帮助编程和代码相关问题的AI助手",
        "system_prompt": "你是一个专业的编程助手，擅长各种编程语言和技术栈。请提供清晰、准确的代码示例和解释。",
        "variables": ["language", "framework"],
        "temperature_override": 0.3,
        "is_active": True,
        "selected_tools": [],
        "use_all_tools": True,
        "preset_dialogues": []
    }
]

# 默认预设方案
DEFAULT_PRESETS = [
    {
        "preset_id": "default_chat",
        "preset_name": "默认对话预设",
        "description": "通用的对话预设方案，适合大多数场景",
        "selected_model": "glm-4",
        "selected_prompt": "default_assistant",
        "selected_memory": "default_buffer",
        "selected_plugins": [],
        "selected_knowledge_bases": [],
        "overrides": {},
        "channel_config": {},
        "is_default": True,
        "is_active": True
    },
    {
        "preset_id": "code_chat",
        "preset_name": "编程助手预设",
        "description": "针对编程场景的优化预设",
        "selected_model": "glm-4-flash",
        "selected_prompt": "code_assistant",
        "selected_memory": "long_buffer",
        "selected_plugins": [],
        "selected_knowledge_bases": [],
        "overrides": {
            "temperature": 0.3
        },
        "channel_config": {},
        "is_default": False,
        "is_active": True
    }
]

# 默认机器人配置
DEFAULT_BOTS = [
    {
        "bot_id": "default_qq_bot",
        "bot_name": "默认QQ机器人",
        "channel_type": "onebot11",
        "preset_id": "default_chat",
        "is_active": True
    }
]

# 默认 OneBot v11 配置
DEFAULT_ONEBOT11_CONFIGS = [
    {
        "bot_id": "default_qq_bot",
        "listen_host": "0.0.0.0",
        "listen_port": 6199,
        "token": None,
        "message_post_format": "array",
        "self_message": False,
        "extra_config": None,
        "is_active": True
    }
]


async def init_database():
    """初始化数据库并插入默认数据"""
    async with AsyncSessionLocal() as session:
        # 插入默认模型配置
        for model_data in DEFAULT_MODELS:
            # 检查是否已存在
            result = await session.execute(
                select(ModelConfig).where(ModelConfig.model_id == model_data["model_id"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                model = ModelConfig(**model_data)
                session.add(model)
        
        await session.commit()
        print("[OK] 默认模型配置已插入")


async def init_default_data(session: AsyncSession = None):
    """初始化默认数据（供 main.py 调用）"""
    async def _init_data(s: AsyncSession):
        # 1. 初始化模型配置
        for model_data in DEFAULT_MODELS:
            result = await s.execute(
                select(ModelConfig).where(ModelConfig.model_id == model_data["model_id"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                model = ModelConfig(**model_data)
                s.add(model)
        
        # 2. 初始化记忆配置
        for memory_data in DEFAULT_MEMORY_CONFIGS:
            result = await s.execute(
                select(MemoryConfig).where(MemoryConfig.memory_id == memory_data["memory_id"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                memory = MemoryConfig(**memory_data)
                s.add(memory)
        
        # 3. 初始化提示词/人格配置
        for prompt_data in DEFAULT_PROMPT_CONFIGS:
            result = await s.execute(
                select(PromptConfig).where(PromptConfig.prompt_id == prompt_data["prompt_id"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                prompt = PromptConfig(**prompt_data)
                s.add(prompt)
        
        # 4. 初始化预设方案
        for preset_data in DEFAULT_PRESETS:
            result = await s.execute(
                select(Preset).where(Preset.preset_id == preset_data["preset_id"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                preset = Preset(**preset_data)
                s.add(preset)

        # 5. 初始化机器人配置
        for bot_data in DEFAULT_BOTS:
            result = await s.execute(
                select(Bot).where(Bot.bot_id == bot_data["bot_id"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                bot = Bot(**bot_data)
                s.add(bot)

        # 6. 初始化 OneBot v11 配置
        for config_data in DEFAULT_ONEBOT11_CONFIGS:
            result = await s.execute(
                select(OneBot11Config).where(OneBot11Config.bot_id == config_data["bot_id"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                config = OneBot11Config(**config_data)
                s.add(config)

        await s.commit()
        print("[OK] 默认模型配置已插入")
        print("[OK] 默认记忆配置已插入")
        print("[OK] 默认提示词配置已插入")
        print("[OK] 默认预设方案已插入")
        print("[OK] 默认机器人配置已插入")
        print("[OK] 默认 OneBot v11 配置已插入")
    
    if session is None:
        # 如果没有传入 session，则创建新的
        async with AsyncSessionLocal() as new_session:
            await _init_data(new_session)
    else:
        # 使用传入的 session
        await _init_data(session)
