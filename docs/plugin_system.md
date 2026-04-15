# 插件系统文档

## 概述

HAXAtom 采用 **Plugin-First** 架构，所有扩展能力（工具、技能、MCP服务）统一通过插件系统管理。

### 核心设计

HAXAtom 的插件系统在 AI 调用层面统一转换为 LangChain Tool，但不同来源的插件有不同的管理和使用方式：

```
┌─────────────────────────────────────────────────────────────┐
│  HAXAtom 插件来源                                            │
├─────────────────────────────────────────────────────────────┤
│  builtin  │ 内置工具，直接可用                               │
│  skill    │ 用户自定义技能，放 skills/ 目录                  │
│  mcp      │ MCP 服务集成，放 mcp/ 目录                       │
│  community│ 社区插件，放 community/ 目录                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  BasePlugin 统一封装                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  tool_adapter.py 转换为 LangChain Tool                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  AI 通过 LangGraph 调用                                     │
└─────────────────────────────────────────────────────────────┘
```

### 目录结构

```
f:\2025python\HAXAtom\backend\app\plugins\
├── builtin/          # 内置插件 (source="builtin")
│   └── builtin_tools.py    # 整合的时间+搜索工具
│
├── skills/          # 用户自定义技能 (source="skill")
│
├── mcp/             # MCP 服务集成 (source="mcp")
│
└── community/       # 社区插件 (source="community")
```

---

## 插件来源分类

| 来源 | 说明 | 目录 |
|------|------|------|
| `builtin` | HAXAtom 内置 | `builtin/` |
| `skill` | 用户自定义技能 | `skills/` |
| `mcp` | MCP 服务集成 | `mcp/` |
| `community` | 第三方社区插件 | `community/` |

---

## 插件基类

所有插件必须继承 `BasePlugin`：

```python
from app.plugins.base import BasePlugin, PluginMetadata, PluginResult

class MyPlugin(BasePlugin):

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_plugin",           # 插件唯一标识
            description="插件功能描述", # AI 看到的描述
            version="1.0.0",
            author="Author",
            category="tool",            # 功能类别
            icon="🔧",
            tags=["tag1", "tag2"],
            source="skill"              # 来源类型
        )

    async def execute(self, params: dict) -> PluginResult:
        # 执行逻辑
        return PluginResult.ok(data={...})
```

---

## PluginMetadata 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | str | ✅ | 插件唯一标识 |
| `description` | str | ✅ | AI 看到的工具描述 |
| `version` | str | ❌ | 版本号，默认 "1.0.0" |
| `author` | str | ❌ | 作者，默认 "Unknown" |
| `category` | str | ❌ | 功能类别，默认 "general" |
| `icon` | str | ❌ | 图标 emoji |
| `tags` | List[str] | ❌ | 标签列表 |
| `source` | str | ❌ | 来源类型，默认 "builtin" |
| `homepage` | str | ❌ | 插件主页（社区插件用） |
| `license` | str | ❌ | 许可证，默认 "MIT" |
| `requirements` | List[str] | ❌ | Python 依赖 |
| `mcp_config` | dict | ❌ | MCP 服务配置 |
| `config_schema` | dict | ❌ | 配置项 JSON Schema |
| `default_config` | dict | ❌ | 默认配置 |

---

## PluginResult 返回格式

```python
class PluginResult:
    success: bool    # 是否成功
    data: Any       # 返回数据
    message: str    # 提示信息
    error: str       # 错误信息

# 成功返回
return PluginResult.ok(data={"key": "value"}, message="操作成功")

# 错误返回
return PluginResult.error(error="error_code", message="错误描述")
```

---

## 工具描述流程

AI 如何看到插件？完整链路：

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Plugin.metadata.description                                  │
│     你的插件文件定义                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. PluginRegistry.register()                                   │
│     插件注册到全局注册表                                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. tool_adapter.py                                            │
│     create_tool_from_plugin()                                   │
│         ↓                                                       │
│     _build_tool_description(metadata)                           │
│         ↓                                                       │
│     LangChain Tool 实例                                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. tool_engine.py                                              │
│     ToolNode 绑定工具到 Agent                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. preset_engine.py                                            │
│     graph.compile() 组合完整工作流                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. AI 调用                                                      │
│     AI 根据 description 决定是否调用工具                          │
└─────────────────────────────────────────────────────────────────┘
```

### _build_tool_description 生成的内容

```python
def _build_tool_description(metadata) -> str:
    """
    最终 AI 看到的描述格式：

    {metadata.description}

    配置参数:
    {config_schema}

    插件类别: {category}
    标签: {tags}
    """
```

### AI 实际看到的描述示例

```
内置工具箱：查询时间/日期(search by keyword)，搜索网络信息(web search)

配置参数:
{
  "properties": {
    "search_engine": {
      "enum": ["baidu", "google", "bing"],
      "default": "baidu",
      "description": "搜索引擎"
    }
  }
}

插件类别: tool
标签: builtin, time, search, web
```

---

## 整合内置工具（builtin_tools.py）

内置工具整合为单个插件，减少 AI 工具调用次数：

### 工具列表

| 工具名 | 功能 | 调用参数 |
|--------|------|----------|
| `time` | 查询当前时间/日期 | `{"tool": "time"}` |
| `search` | 搜索网络信息 | `{"tool": "search", "query": "关键词"}` |

### AI 调用示例

```
用户: 现在几点了？

AI 判断: 需要查询时间
AI 调用工具:
{
  "name": "builtin_tools",
  "arguments": {"tool": "time"}
}

工具返回:
{
  "success": true,
  "data": {
    "time": "14:30:25",
    "date": "2026-04-15",
    "weekday": "星期二"
  }
}

AI 回复: 现在是 2026年4月15日 14:30:25，星期二
```

---

## 加载器 (PluginLoader)

### 加载方法

```python
from app.plugins.loader import loader

# 加载所有类型
loader.load_all_plugins()

# 分开加载
loader.load_builtin_plugins()    # 内置
loader.load_skills_plugins()      # 用户技能
loader.load_mcp_plugins()         # MCP
loader.load_community_plugins()  # 社区
```

### 从目录加载

```python
# 从指定目录加载插件
loader.load_from_directory("/path/to/plugins")
```

---

## 注册表 (PluginRegistry)

### 核心方法

```python
from app.plugins.registry import registry

# 注册插件
registry.register(MyPluginClass)

# 获取插件
plugin = registry.get("plugin_name")

# 获取元数据
metadata = registry.get_metadata("plugin_name")

# 列出所有插件
all_plugins = registry.list_plugins()

# 按来源查询
builtin = registry.list_by_source("builtin")
skills = registry.list_by_source("skill")

# 按类别查询
tools = registry.list_by_category("tool")

# 获取所有来源类型
sources = registry.get_all_sources()

# 启用/禁用
registry.enable("plugin_name")
registry.disable("plugin_name")
```

---

## 转换为 LangChain Tool

```python
from app.plugins.tool_adapter import create_tool_from_plugin, get_tools_for_preset

# 转换单个插件
tool = create_tool_from_plugin("builtin_tools")

# 根据预设获取工具列表
tools = get_tools_for_preset(["builtin_tools", "other_plugin"])
```

---

## 创建新插件

### 1. 创建插件文件

在对应目录创建，如 `skills/stock_query.py`：

```python
"""
股票查询插件
"""
from typing import Any, Dict

from app.plugins.base import BasePlugin, PluginMetadata, PluginResult


class StockQueryPlugin(BasePlugin):

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="stock_query",
            description="查询股票价格和涨跌情况，支持A股、港股、美股",
            version="1.0.0",
            author="YourName",
            category="tool",
            icon="📈",
            tags=["stock", "finance", "quote"],
            source="skill",
            config_schema={
                "type": "object",
                "properties": {
                    "market": {
                        "type": "string",
                        "enum": ["A股", "港股", "美股"],
                        "description": "股票市场"
                    }
                }
            }
        )

    async def execute(self, params: Dict[str, Any]) -> PluginResult:
        stock_code = params.get("code", "")
        market = params.get("market", "A股")

        # 查询逻辑
        data = {
            "code": stock_code,
            "price": 100.50,
            "change": 2.35,
            "change_percent": 2.39
        }

        return PluginResult.ok(data=data)

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        if not params.get("code"):
            return False, "股票代码不能为空"
        return True, None
```

### 2. 注册插件

```python
from app.plugins.loader import loader

# 加载新插件
loader.load_skills_plugins()
# 或重新加载所有
loader.load_all_plugins()
```

### 3. 在预设中启用

通过 API 或管理界面将插件添加到预设的 `selected_plugins` 中。

---

## MCP 插件开发

MCP (Model Context Protocol) 插件放置在 `mcp/` 目录：

```python
"""
MCP 文件系统插件示例
"""
from typing import Any, Dict

from app.plugins.base import BasePlugin, PluginMetadata, PluginResult


class FilesystemPlugin(BasePlugin):

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="filesystem",
            description="读写本地文件系统",
            version="1.0.0",
            author="HAXAtom",
            category="tool",
            source="mcp",
            mcp_config={
                "server": "filesystem",
                "command": "npx",
                "args": ["@modelcontextprotocol/server-filesystem", "/path/to/dir"]
            }
        )

    async def execute(self, params: Dict[str, Any]) -> PluginResult:
        operation = params.get("operation")
        # MCP 调用逻辑
        ...
```

---

## 最佳实践

### 1. 整合小型工具

类似的内置工具整合为一个插件，减少 AI 选择负担：

```python
class BuiltinToolsPlugin(BasePlugin):
    """整合多个小工具"""

    async def execute(self, params: dict) -> PluginResult:
        tool = params.get("tool")
        if tool == "time":
            return self._get_time()
        elif tool == "calc":
            return self._calc(params)
        ...
```

### 2. 清晰的描述

`description` 是 AI 决策依据，必须清晰：

```python
# ❌ 不好
description="工具"

# ✅ 好
description="计算数学表达式，支持 + - * / ^ 运算符，如 1+2*3"
```

### 3. 参数验证

实现 `validate_params` 减少 AI 调用失败：

```python
def validate_params(self, params: dict) -> tuple[bool, str]:
    if not params.get("required_field"):
        return False, "必填参数 missing"
    return True, None
```

### 4. 错误处理

```python
async def execute(self, params: dict) -> PluginResult:
    try:
        # 业务逻辑
        return PluginResult.ok(data={...})
    except ValueError as e:
        return PluginResult.error(error="invalid_input", message=str(e))
    except Exception as e:
        return PluginResult.error(error="internal_error", message="服务异常")
```

---

## 调试技巧

### 查看已加载的插件

```python
from app.plugins.registry import registry

print("所有插件:", registry.list_plugins())
print("内置插件:", registry.list_by_source("builtin"))
print("技能插件:", registry.list_by_source("skill"))
```

### 查看工具描述

```python
from app.plugins.tool_adapter import create_tool_from_plugin

tool = create_tool_from_plugin("builtin_tools")
print("工具描述:", tool.description)
```

### 测试插件执行

```python
from app.plugins.registry import registry

plugin = registry.get("builtin_tools")
result = await plugin.execute({"tool": "time"})
print(result)
```

---

## LangGraph 工作流

### 完整请求流程

当用户通过 API 发起对话请求时，完整的处理流程：

```
┌─────────────────────────────────────────────────────────────────┐
│  1. API 入口 (chat.py)                                          │
│     POST /api/v1/chat/completions 或 /completions/stream        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. PresetEngine.chat()                                         │
│     - 加载预设方案配置                                           │
│     - 获取模型、提示词、插件、记忆、RAG配置                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. 构建 LangGraph StateGraph                                    │
│     - retrieval 节点：RAG 检索                                  │
│     - agent 节点：LLM 对话                                      │
│     - tools 节点：插件/工具执行                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. StateGraph 执行                                              │
│     ┌──────────────────────────────────────────────────────────┐ │
│     │  retrieval ──→ agent ──→ tools                          │ │
│     │                      ↑                                  │ │
│     │                      └──────── 循环 ──────────────────────│ │
│     └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. 流式响应返回                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 节点说明

| 节点 | 组件 | 作用 |
|------|------|------|
| `retrieval` | RAGEngine | 从知识库检索相关内容 |
| `agent` | LLM (智谱GLM) | 核心对话，理解意图，决定下一步 |
| `tools` | ToolNode | 执行插件/工具，返回结果 |

### LangGraph 条件边

```
Agent 判断 ──→ needs_tool_call = True ──→ tools 节点
     ↓
needs_tool_call = False ──→ 直接返回用户

Tools 执行后 ──→ 返回 Agent 继续处理
     ↓
step_count >= max_steps ──→ 结束
```

### 代码位置

| 组件 | 文件 | 说明 |
|------|------|------|
| API 入口 | `app/api/v1/endpoints/chat.py` | `chat_completion()` / `chat_completion_stream()` |
| 核心引擎 | `app/core/preset_engine.py` | `PresetEngine.chat()` 构建 StateGraph |
| 状态类型 | `app/core/state_types.py` | `AgentState` 定义 |
| 工具引擎 | `app/core/tool_engine.py` | `ToolEngine` / `ToolNode` |
| RAG 引擎 | `app/core/rag_engine.py` | `RAGEngine` 检索 |
| 插件适配 | `app/plugins/tool_adapter.py` | `create_tool_from_plugin()` |

### 工具调用流程

```
1. Agent (LLM) 看到用户消息 + 工具描述
         ↓
2. LLM 判断：需要调用工具
         ↓
3. LLM 输出 AIMessage(tool_calls=[...])
         ↓
4. should_call_tools() 返回 True
         ↓
5. ToolNode 执行工具
         ↓
6. 工具结果转为 ToolMessage
         ↓
7. 返回 Agent 继续处理
         ↓
8. Agent 最终回复用户
```

### 启用/禁用控制

| 功能 | 控制方式 | API 参数 |
|------|----------|----------|
| 工具调用 | `enable_tools` | `true` 启用 / `false` 禁用 |
| RAG 检索 | `enable_rag` | `true` 启用 / `false` 禁用 |
| 记忆系统 | `enable_memory` | `true` 启用 / `false` 禁用 |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-04-15 | 初始文档，整合插件来源分类 |
