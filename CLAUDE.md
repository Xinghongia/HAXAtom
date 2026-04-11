# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HAXAtom is a full-stack AI agent management platform built with "atomic decoupling, LEGO-style assembly" architecture. The core concept separates agent capabilities into five independent resource pools that can be combined via preset configurations.

**Core Design Principles:**
1. **Atomic Decoupling**: Model, Prompt, Plugin, Knowledge Base, and Memory are completely independent
2. **Resource Poolization**: All configurations are stored as reusable atomic resources
3. **LEGO-style Assembly**: Presets combine resources from pools dynamically
4. **Lightweight Deployment**: Single exe or Docker, no middleware required
5. **Multi-channel Distribution**: One preset works across Web, Feishu, QQ, Telegram, etc.

## Tech Stack & Versions (Strict)

**Backend:**
- Python 3.11+
- FastAPI 0.115+ with Uvicorn
- **LangChain 0.3+** (MUST use latest stable version)
- **LangGraph 0.2+** (for agent orchestration, replaces AgentExecutor)
- SQLAlchemy 2.0+ (async) with aiosqlite
- ChromaDB 0.5+ (local vector store)
- Pydantic 2.9+

**Frontend:**
- Vue 3.4+ + Vite 5+
- Element Plus 2.13+
- Vue Router 4+
- Axios

**Critical Constraints:**
- NEVER use deprecated APIs: `LLMChain`, `SequentialChain`, `AgentExecutor`, `ConversationChain`
- MUST use LCEL syntax (`|` operator) for all chains
- MUST use LangGraph `StateGraph` for agent workflows
- Memory MUST use `RunnableWithMessageHistory` or LangGraph persistence

## Development Commands

### Backend (Poetry)
```bash
# Install dependencies
cd backend
poetry install

# Run development server
poetry run uvicorn app.main:app --reload

# Run tests
poetry run pytest

# Database migrations
alembic upgrade head              # Apply migrations
alembic revision --autogenerate   # Create new migration

# Code formatting
poetry run black .
poetry run isort .
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # Development server
npm run build     # Production build
```

## Architecture

### Backend Structure

```
backend/app/
├── main.py                 # FastAPI app entry, lifecycle, middleware
├── config.py               # Pydantic Settings for config
├── core/
│   ├── preset_engine.py    # CORE: LangGraph StateGraph for agent workflow
│   ├── state_types.py      # AgentState, RAGState, ToolState definitions
│   ├── tool_engine.py      # Tool calling with LangGraph ToolNode
│   ├── rag_engine.py       # RAG retrieval with LCEL
│   └── langsmith_tracer.py # LangSmith integration
├── models/                 # SQLAlchemy models (5 resource pools + presets + conversations)
├── schemas/                # Pydantic schemas for API
├── api/v1/endpoints/       # REST API endpoints
├── services/               # Business logic (memory, conversation, vector store)
├── plugins/
│   ├── base.py             # BasePlugin interface
│   ├── registry.py         # PluginRegistry singleton
│   ├── loader.py           # Plugin loading
│   └── builtin/            # Built-in plugins (time, search, calculator)
└── db/
    ├── session.py          # Async database session
    └── migrations/         # Alembic migrations
```

### Core Engines

**PresetEngine** (`backend/app/core/preset_engine.py`):
- Loads preset and validates all referenced resources
- Dynamically builds LangGraph StateGraph with nodes: `retrieval` → `agent` → `tools`
- Uses `create_initial_state()` to prepare conversation state
- Implements streaming via `graph.astream_events()`

**RAGEngine** (`backend/app/core/rag_engine.py`):
- Multi-knowledge base retrieval with ChromaDB
- LCEL chains: `prompt | model | parser`
- Context formatting for injection into system prompts

**ToolEngine** (`backend/app/core/tool_engine.py`):
- Creates LangGraph `ToolNode` from plugins
- Conditional edges: `should_continue_to_tools()` determines flow
- Tool execution with automatic result formatting

### Plugin System

All plugins inherit from `BasePlugin`:
- Implement `metadata` property (PluginMetadata)
- Implement `async execute(params: Dict) -> PluginResult`
- Register via `PluginRegistry`

Example in `backend/app/plugins/builtin/`:
- `time_plugin.py`: Current time
- `search_plugin.py`: Web search
- `calculator_plugin.py`: Basic calculations

### Five Resource Pools (Database Tables)

1. **Model Config** (`model_configs`): Stores LLM/Embedding configs. `model_name` is JSON array (supports multiple models per provider like `["glm-4", "glm-5"]`)
2. **Prompt Config** (`prompt_configs`): System prompts and variables
3. **Plugin Config** (`plugin_configs`): Plugin configuration
4. **Knowledge Base** (`knowledge_bases`): Vector store collections
5. **Memory Config** (`memory_configs`): Memory strategies (buffer_window, summary, token_buffer)

**Presets** (`presets` table):
- References resources by ID, not foreign keys (for flexibility)
- `selected_model`: Stores actual model name (e.g., "glm-4")
- `selected_plugins`, `selected_knowledge_bases`: JSON arrays
- `overrides`: Per-preset parameter overrides

### State Management

**AgentState** (`backend/app/core/state_types.py`):
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    input: str
    preset_id: str
    session_id: Optional[str]
    retrieved_context: Optional[str]
    needs_retrieval: bool
    tool_results: Optional[List[Dict]]
    needs_tool_call: bool
    step_count: int
    max_steps: int
    overrides: Optional[Dict]
    error: Optional[str]
```

### API Endpoints

All under `/api/v1/`:
- `/models` - Model configuration CRUD
- `/prompts` - Prompt configuration CRUD
- `/presets` - Preset CRUD + validation
- `/plugins` - Plugin management
- `/knowledge-bases` - Knowledge base CRUD + document upload
- `/memories` - Memory configuration CRUD
- `/chat/completions` - Non-streaming chat
- `/chat/completions/stream` - SSE streaming chat
- `/chat/conversations` - Conversation management

### Frontend Structure

```
frontend/src/
├── views/
│   ├── bot/
│   │   ├── BotView.vue           # Main admin layout
│   │   └── pages/                # Resource pool management pages
│   │       ├── ModelProviderView.vue
│   │       ├── PersonalityView.vue
│   │       ├── KnowledgeBasePage.vue
│   │       ├── PresetPage.vue
│   │       ├── MemoryConfigPage.vue
│   │       └── PluginsPage.vue
│   └── chat/
│       └── ChatView.vue          # Chat interface
├── components/
│   ├── preset/                   # Preset editor components
│   ├── model-provider/           # Model config components
│   └── personality/              # Personality/prompt components
├── api/                          # API client (axios)
├── router/                       # Vue Router config
└── locales/                      # i18n (zh-CN, en-US)
```

## Key Implementation Notes

### LCEL Chain Pattern
```python
# CORRECT - LCEL syntax
prompt = ChatPromptTemplate.from_messages([...])
chain = prompt | model | parser
result = await chain.ainvoke({...})

# WRONG - Deprecated
chain = LLMChain(llm=model, prompt=prompt)
```

### LangGraph Pattern
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")
graph = workflow.compile(checkpointer=MemorySaver())
```

### Memory System
- Conversations stored in `conversations` table
- Messages in JSON column `messages: List[Dict[role, content, ...]]`
- Memory service supports: buffer_window (sliding), summary (condensed), token_buffer (token-limited)
- History injected via `MemoryService.add_memory_to_prompt()`

### LangSmith Integration
Enable via environment variables:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=haxatom
```

Metadata added to graph execution includes: preset_id, session_id, enable_rag, enable_tools, model_id

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

Migrations auto-generated from SQLAlchemy models in `backend/app/models/`.

## Common Patterns

### Adding a New Plugin
1. Create class in `backend/app/plugins/builtin/` extending `BasePlugin`
2. Implement `metadata` and `execute()`
3. Register in `app/plugins/loader.py` or via API

### Adding a New Resource Pool
1. Create model in `backend/app/models/`
2. Create schema in `backend/app/schemas/`
3. Create service in `backend/app/services/`
4. Create API endpoint in `backend/app/api/v1/endpoints/`
5. Run `alembic revision --autogenerate`
6. Create frontend page in `frontend/src/views/bot/pages/`

### Streaming Response
Use `EventSourceResponse` from `sse-starlette`:
```python
async def event_generator():
    async for chunk in engine.chat(..., stream=True):
        yield {"event": "message", "data": json.dumps({"content": chunk})}
return EventSourceResponse(event_generator())
```

## Configuration

Backend config via `.env` file (see `app/config.py`):
- `database_url`: SQLite connection string
- `chroma_persist_dir`: ChromaDB storage
- `langsmith_tracing`: Enable/disable LangSmith
- `log_level`: Logging level

## Testing

```bash
cd backend
poetry run pytest                    # All tests
poetry run pytest tests/test_core.py # Specific file
poetry run pytest -v                 # Verbose output
```

Tests use pytest-asyncio for async test support.
