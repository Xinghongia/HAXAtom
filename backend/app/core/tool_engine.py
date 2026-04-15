"""
工具调用引擎

基于 LangGraph ToolNode 实现的工具调用引擎
支持工具调用决策、执行、结果回传
"""

import json
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.state_types import AgentState, ToolState
from app.plugins.tool_adapter import get_tools_for_preset


class ToolEngine:
    """
    工具调用引擎
    
    职责：
    1. 根据预设方案加载可用工具
    2. 创建 LangGraph ToolNode
    3. 处理工具调用请求
    4. 格式化工具执行结果
    """
    
    def __init__(self, db_session: AsyncSession, plugin_ids: List[str]):
        self.db = db_session
        self.plugin_ids = plugin_ids
        self.tools: List[BaseTool] = []
        self._initialize_tools()
    
    def _initialize_tools(self):
        """初始化工具列表"""
        self.tools = get_tools_for_preset(self.plugin_ids)
    
    def get_tools(self) -> List[BaseTool]:
        """获取可用工具列表"""
        return self.tools
    
    def has_tools(self) -> bool:
        """检查是否有可用工具"""
        return len(self.tools) > 0
    
    def create_tool_node(self) -> Optional[ToolNode]:
        """
        创建 LangGraph ToolNode
        
        Returns:
            Optional[ToolNode]: 工具节点，如果没有可用工具则返回 None
        """
        if not self.tools:
            return None
        
        return ToolNode(self.tools)
    
    def should_call_tools(self, state: AgentState) -> bool:
        """
        判断是否需要调用工具
        
        检查最后一条 AI 消息是否包含工具调用请求
        
        Args:
            state: 当前状态
            
        Returns:
            bool: 是否需要调用工具
        """
        messages = state.get("messages", [])
        if not messages:
            return False
        
        last_message = messages[-1]
        
        # 检查是否是 AIMessage 且包含 tool_calls
        if isinstance(last_message, AIMessage):
            tool_calls = getattr(last_message, "tool_calls", None)
            if tool_calls:
                return True
        
        return False
    
    async def execute_tools(self, state: AgentState) -> AgentState:
        """
        执行工具调用
        
        Args:
            state: 当前状态
            
        Returns:
            AgentState: 更新后的状态（包含工具执行结果）
        """
        tool_node = self.create_tool_node()
        if not tool_node:
            return state
        
        try:
            # 执行工具
            result = await tool_node.ainvoke(state)
            return result
        except Exception as e:
            # 工具执行出错，添加错误消息
            error_message = ToolMessage(
                content=f"工具执行错误: {str(e)}",
                tool_call_id="error",
                name="error"
            )
            messages = list(state.get("messages", []))
            messages.append(error_message)
            
            return AgentState(
                messages=messages,
                input=state["input"],
                preset_id=state["preset_id"],
                session_id=state.get("session_id"),
                retrieved_context=state.get("retrieved_context"),
                needs_retrieval=state.get("needs_retrieval", False),
                tool_results=None,
                needs_tool_call=False,
                step_count=state.get("step_count", 0) + 1,
                max_steps=state.get("max_steps", 10),
                overrides=state.get("overrides"),
                error=str(e)
            )
    
    def format_tool_results(self, tool_messages: List[ToolMessage]) -> str:
        """
        格式化工具执行结果
        
        Args:
            tool_messages: 工具消息列表
            
        Returns:
            str: 格式化后的结果文本
        """
        results = []
        for msg in tool_messages:
            try:
                # 尝试解析 JSON
                data = json.loads(msg.content)
                if data.get("success"):
                    results.append(f"[{msg.name}] 执行成功: {data.get('message', '')}")
                    if data.get("data"):
                        results.append(f"结果: {json.dumps(data['data'], ensure_ascii=False)}")
                else:
                    results.append(f"[{msg.name}] 执行失败: {data.get('error', '未知错误')}")
            except json.JSONDecodeError:
                results.append(f"[{msg.name}] {msg.content}")
        
        return "\n".join(results)
    
    def create_tools_system_prompt(self) -> str:
        """
        创建工具相关的系统提示词
        
        Returns:
            str: 系统提示词
        """
        if not self.tools:
            return ""
        
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(
                f"- {tool.name}: {tool.description}"
            )
        
        return f"""你可以使用以下工具来帮助回答用户问题：

{chr(10).join(tool_descriptions)}

如果需要使用工具，请明确调用。工具调用格式：
{{"name": "工具名称", "arguments": {{"参数名": "参数值"}}}}"""


# LangGraph 节点函数

def create_tool_decision_node(tool_engine: ToolEngine):
    """
    创建工具决策节点
    
    判断是否需要调用工具，并更新状态
    """
    async def _tool_decision(state: AgentState) -> AgentState:
        """工具决策逻辑"""
        needs_tool = tool_engine.should_call_tools(state)
        
        return AgentState(
            messages=state["messages"],
            input=state["input"],
            preset_id=state["preset_id"],
            session_id=state.get("session_id"),
            retrieved_context=state.get("retrieved_context"),
            needs_retrieval=state.get("needs_retrieval", False),
            tool_results=state.get("tool_results"),
            needs_tool_call=needs_tool,
            step_count=state.get("step_count", 0),
            max_steps=state.get("max_steps", 10),
            overrides=state.get("overrides"),
            error=state.get("error")
        )
    
    return _tool_decision


def create_tool_execution_node(tool_engine: ToolEngine):
    """
    创建工具执行节点
    
    执行工具调用并更新状态
    """
    async def _tool_execution(state: AgentState) -> AgentState:
        """工具执行逻辑"""
        if not state.get("needs_tool_call"):
            return state
        
        return await tool_engine.execute_tools(state)
    
    return _tool_execution


# 条件边函数

def should_continue_to_tools(state: AgentState) -> str:
    """
    条件边：是否应该调用工具

    Returns:
        str: "tools" 或 "agent"
    """
    import logging
    logger = logging.getLogger(__name__)

    # 检查步骤限制
    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", 10)

    if step_count >= max_steps:
        return "agent"  # 超过最大步骤，直接返回给 agent

    # 检查最后一条消息
    messages = state.get("messages", [])
    if not messages:
        return "agent"

    last_message = messages[-1]

    # 如果是 AIMessage 且有 tool_calls，则调用工具
    if isinstance(last_message, AIMessage):
        tool_calls = getattr(last_message, "tool_calls", None)
        logger.info(f"[should_continue_to_tools] AIMessage tool_calls: {tool_calls}")
        if tool_calls:
            return "tools"

    logger.info(f"[should_continue_to_tools] last_message type: {type(last_message)}, no tool_calls")
    return "agent"


def should_continue_after_tools(state: AgentState) -> str:
    """
    条件边：工具执行后是否继续

    Returns:
        str: "agent" 或 "end"
    """
    import logging
    logger = logging.getLogger(__name__)

    # 检查是否有错误
    if state.get("error"):
        logger.info(f"[should_continue_after_tools] 有错误: {state.get('error')}")
        return "agent"  # 有错误，返回给 agent 处理

    # 检查消息
    messages = state.get("messages", [])
    logger.info(f"[should_continue_after_tools] messages 数量: {len(messages)}")
    if messages:
        last_msg = messages[-1]
        logger.info(f"[should_continue_after_tools] 最后一条消息 type: {type(last_msg).__name__}")
        if hasattr(last_msg, 'content'):
            content = last_msg.content
            logger.info(f"[should_continue_after_tools] 最后一条消息 content 长度: {len(content) if content else 0}")
            if content and len(content) < 500:
                logger.info(f"[should_continue_after_tools] 最后一条消息 content: {content[:500]}")

    # 检查步骤限制
    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", 10)

    if step_count >= max_steps:
        return "end"  # 超过最大步骤，结束

    return "agent"  # 返回给 agent 继续处理
