"""
插件到 LangChain Tool 的适配器

将 HAXAtom 插件转换为 LangChain Tool 格式，支持 Agent 调用
"""

import json
from typing import Any, Dict, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.plugins import registry
from app.plugins.base import BasePlugin


class PluginToolSchema(BaseModel):
    """插件工具参数 Schema"""
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="插件执行参数。必须包含 tool 字段指定子工具类型，可选包含其他参数如 query。"
    )


def create_tool_from_plugin(plugin_id: str) -> Optional[BaseTool]:
    """
    将 HAXAtom 插件转换为 LangChain Tool

    Args:
        plugin_id: 插件ID

    Returns:
        Optional[BaseTool]: LangChain Tool 实例，如果插件不存在或未启用则返回 None
    """
    plugin = registry.get(plugin_id)
    metadata = registry.get_metadata(plugin_id)

    if not plugin or not metadata:
        return None

    # 检查插件是否启用
    if not plugin.enabled:
        return None
    
    # 创建动态 Tool 类
    class DynamicPluginTool(BaseTool):
        """动态插件工具"""
        
        name: str = metadata.name
        description: str = _build_tool_description(metadata)
        args_schema: Type[BaseModel] = PluginToolSchema
        
        def _run(self, params: Dict[str, Any]) -> str:
            """同步执行（不支持，插件都是异步的）"""
            raise NotImplementedError("Plugin tools only support async execution")
        
        async def _arun(self, params: Dict[str, Any]) -> str:
            """异步执行插件"""
            # 验证参数
            valid, error = plugin.validate_params(params)
            if not valid:
                return json.dumps({
                    "success": False,
                    "error": error,
                    "message": f"参数验证失败: {error}"
                }, ensure_ascii=False)
            
            # 执行插件
            result = await plugin.execute(params)
            
            # 构建结果字典（确保所有值可序列化）
            # 过滤掉非字符串的 error（如类方法绑定）
            error_val = result.error
            if error_val is not None and not isinstance(error_val, str):
                error_val = None
            
            result_dict = {
                "success": bool(result.success) if result.success is not None else True,
                "data": result.data if result.data is not None else {},
                "message": str(result.message) if result.message else "",
                "error": error_val
            }
            
            # 返回 JSON 字符串
            return json.dumps(result_dict, ensure_ascii=False, default=str)
    
    return DynamicPluginTool()


def get_tools_for_preset(plugin_ids: list[str]) -> list[BaseTool]:
    """
    根据预设方案的插件列表获取对应的 LangChain Tools
    
    Args:
        plugin_ids: 预设方案中配置的插件ID列表
        
    Returns:
        list[BaseTool]: LangChain Tool 列表
    """
    tools = []
    for plugin_id in plugin_ids:
        tool = create_tool_from_plugin(plugin_id)
        if tool:
            tools.append(tool)
    return tools


def _build_tool_description(metadata) -> str:
    """
    构建工具描述

    这个描述会被 LLM 用来决定是否调用该工具
    """
    desc = f"{metadata.description}\n\n"

    # 针对 builtin_tools 提供更详细的子工具说明
    if metadata.name == "builtin_tools":
        desc += "【重要】params 参数结构：\n"
        desc += "- 查询时间: params = {\"tool\": \"time\"}\n"
    else:
        # 获取配置schema（如果是方法则跳过）
        config_schema = metadata.config_schema
        if config_schema and not callable(config_schema):
            desc += "配置参数:\n"
            desc += json.dumps(config_schema, ensure_ascii=False, indent=2)
            desc += "\n\n"

    desc += f"插件类别: {metadata.category}\n"
    desc += f"标签: {', '.join(metadata.tags)}"

    return desc


class ToolCallingManager:
    """
    工具调用管理器
    
    管理预设方案的工具调用生命周期
    """
    
    def __init__(self, preset_config: dict):
        """
        初始化工具调用管理器
        
        Args:
            preset_config: 预设方案配置
        """
        self.preset_config = preset_config
        self.tools: list[BaseTool] = []
        self._initialize_tools()
    
    def _initialize_tools(self):
        """根据预设配置初始化工具"""
        plugin_ids = self.preset_config.get("selected_plugins", [])
        self.tools = get_tools_for_preset(plugin_ids)
    
    def get_tools(self) -> list[BaseTool]:
        """获取当前预设的所有工具"""
        return self.tools
    
    def has_tools(self) -> bool:
        """检查是否有可用工具"""
        return len(self.tools) > 0
