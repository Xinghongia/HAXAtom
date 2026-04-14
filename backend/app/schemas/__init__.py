"""
Pydantic Schema 包

导出所有 Schema 类
"""

from app.schemas.bot import (
    BotCreate,
    BotDetailResponse,
    BotResponse,
    BotUpdate,
    OneBot11ConfigCreate,
    OneBot11ConfigSchema,
    OneBot11ConfigUpdate,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    ConversationCreate,
    ConversationDetail,
    ConversationInDB,
    ConversationList,
    ConversationUpdate,
    FeedbackRequest,
    Message,
)
from app.schemas.common import (
    CountResponse,
    IDResponse,
    ListResponse,
    PaginationParams,
    ResponseBase,
    TimestampMixin,
)
from app.schemas.memory_config import (
    MemoryConfigCreate,
    MemoryConfigList,
    MemoryConfigResponse,
    MemoryConfigUpdate,
)
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigInDB,
    ModelConfigList,
    ModelConfigResponse,
    ModelConfigUpdate,
    ModelParams,
)
from app.schemas.preset import (
    ChannelConfig,
    KnowledgeBaseInfo,
    MemoryInfo,
    ModelInfo,
    OverrideConfig,
    PluginInfo,
    PresetCloneRequest,
    PresetCreate,
    PresetDetail,
    PresetInDB,
    PresetList,
    PresetUpdate,
    PromptInfo,
)
from app.schemas.prompt_config import (
    PromptConfigCreate,
    PromptConfigInDB,
    PromptConfigList,
    PromptConfigUpdate,
)

__all__ = [
    # Common
    "ResponseBase",
    "ListResponse",
    "PaginationParams",
    "IDResponse",
    "CountResponse",
    "TimestampMixin",
    # Bot
    "BotCreate",
    "BotUpdate",
    "BotResponse",
    "BotDetailResponse",
    "OneBot11ConfigSchema",
    "OneBot11ConfigCreate",
    "OneBot11ConfigUpdate",
    # Model Config
    "ModelParams",
    "ModelConfigCreate",
    "ModelConfigUpdate",
    "ModelConfigInDB",
    "ModelConfigResponse",
    "ModelConfigList",
    # Prompt Config
    "PromptConfigCreate",
    "PromptConfigUpdate",
    "PromptConfigInDB",
    "PromptConfigList",
    # Memory Config
    "MemoryConfigCreate",
    "MemoryConfigUpdate",
    "MemoryConfigResponse",
    "MemoryConfigList",
    # Preset
    "ChannelConfig",
    "OverrideConfig",
    "PresetCreate",
    "PresetUpdate",
    "PresetInDB",
    "PresetDetail",
    "PresetList",
    "PresetCloneRequest",
    # Preset 资源信息
    "ModelInfo",
    "PromptInfo",
    "MemoryInfo",
    "KnowledgeBaseInfo",
    "PluginInfo",
    # Chat
    "Message",
    "ChatRequest",
    "ChatResponse",
    "ChatStreamChunk",
    "ConversationInDB",
    "ConversationDetail",
    "ConversationList",
    "ConversationCreate",
    "ConversationUpdate",
    "FeedbackRequest",
]
