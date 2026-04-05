"""
预设引擎 (PresetEngine)

基于 LangGraph StateGraph 实现的核心引擎
完全遵循架构图设计，支持 RAG、工具调用、记忆系统
"""

import logging
import os
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rag_engine import RAGEngine
from app.core.state_types import AgentState, create_initial_state
from app.core.tool_engine import (
    ToolEngine,
    should_continue_to_tools,
    should_continue_after_tools,
)
from app.models import (
    ModelConfig, 
    Preset, 
    PromptConfig, 
    PluginConfig, 
    KnowledgeBase,
    MemoryConfig
)
from app.services.memory_service import MemoryService


class PresetEngine:
    """
    预设引擎 - LangGraph 实现
    
    核心职责：
    1. 根据 preset_id 加载预设方案
    2. 从五大资源池获取原子化配置
    3. 动态组装 LangGraph 工作流
    4. 执行对话并返回结果
    
    架构设计：
    - 原子化解耦：每个资源独立配置，通过ID引用
    - 乐高式拼装：运行时动态组合成 StateGraph
    - 状态驱动：使用 AgentState 在各节点间传递状态
    - 循环支持：支持工具调用的循环决策
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self._model_cache: Dict[str, BaseChatModel] = {}
        self._graph_cache: Dict[str, StateGraph] = {}
        self.logger = logging.getLogger(__name__)
    
    async def load_preset(self, preset_id: str) -> Preset:
        """加载预设方案"""
        self.logger.info(f"[PresetEngine] 加载预设方案: {preset_id}")
        
        result = await self.db.execute(
            select(Preset).where(Preset.preset_id == preset_id, Preset.is_active == True)
        )
        preset = result.scalar_one_or_none()
        
        if not preset:
            self.logger.error(f"[PresetEngine] 预设方案不存在: {preset_id}")
            raise ValueError(f"预设方案 '{preset_id}' 不存在或未激活")
        
        self.logger.info(f"[PresetEngine] 预设方案加载成功: {preset.preset_name}")
        return preset
    
    async def _get_memory_config(self, preset: Preset) -> Optional[MemoryConfig]:
        """
        获取记忆配置
        
        Args:
            preset: 预设方案对象
            
        Returns:
            Optional[MemoryConfig]: 记忆配置对象或None
        """
        if not preset.selected_memory:
            return None
        
        result = await self.db.execute(
            select(MemoryConfig).where(
                MemoryConfig.memory_id == preset.selected_memory,
                MemoryConfig.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def _load_conversation_history(
        self,
        session_id: str,
        memory_config: Optional[MemoryConfig] = None
    ) -> List[Dict[str, str]]:
        """
        加载对话历史
        
        Args:
            session_id: 会话ID
            memory_config: 记忆配置
            
        Returns:
            List[Dict[str, str]]: 历史消息列表
        """
        if not session_id:
            return []
        
        memory_service = MemoryService(self.db)
        
        if memory_config:
            # 使用配置的记忆策略
            messages = await memory_service.get_conversation_history(
                session_id,
                limit=memory_config.memory_params.get("window_size", 20)
            )
        else:
            # 默认使用滑动窗口
            messages = await memory_service.get_conversation_history(
                session_id,
                limit=10
            )
        
        return messages
    
    async def validate_preset_resources(self, preset: Preset) -> None:
        """
        校验预设方案引用的所有资源是否存在且可用
        
        校验内容：
        1. 模型ID -> 模型池
        2. 提示词ID -> 提示词池
        3. 插件ID列表 -> 插件池
        4. 知识库ID列表 -> 知识库池
        5. 记忆ID -> 记忆池
        
        Args:
            preset: 预设方案对象
            
        Raises:
            ValueError: 当某个资源不存在或未激活时
        """
        errors = []
        
        # 1. 校验模型
        if preset.selected_model:
            result = await self.db.execute(
                select(ModelConfig).where(
                    ModelConfig.model_id == preset.selected_model,
                    ModelConfig.is_active == True
                )
            )
            if not result.scalar_one_or_none():
                errors.append(f"模型 '{preset.selected_model}' 不存在或未激活")
        else:
            errors.append("预设方案未配置模型")
        
        # 2. 校验提示词（可选）
        if preset.selected_prompt:
            result = await self.db.execute(
                select(PromptConfig).where(
                    PromptConfig.prompt_id == preset.selected_prompt,
                    PromptConfig.is_active == True
                )
            )
            if not result.scalar_one_or_none():
                errors.append(f"提示词 '{preset.selected_prompt}' 不存在或未激活")
        
        # 3. 校验插件列表
        if preset.selected_plugins:
            for plugin_id in preset.selected_plugins:
                result = await self.db.execute(
                    select(PluginConfig).where(
                        PluginConfig.plugin_id == plugin_id,
                        PluginConfig.is_active == True
                    )
                )
                if not result.scalar_one_or_none():
                    errors.append(f"插件 '{plugin_id}' 不存在或未激活")
        
        # 4. 校验知识库列表
        if preset.selected_knowledge_bases:
            for kb_id in preset.selected_knowledge_bases:
                result = await self.db.execute(
                    select(KnowledgeBase).where(
                        KnowledgeBase.kb_id == kb_id,
                        KnowledgeBase.is_active == True
                    )
                )
                if not result.scalar_one_or_none():
                    errors.append(f"知识库 '{kb_id}' 不存在或未激活")
        
        # 5. 校验记忆配置（可选）
        if preset.selected_memory:
            result = await self.db.execute(
                select(MemoryConfig).where(
                    MemoryConfig.memory_id == preset.selected_memory,
                    MemoryConfig.is_active == True
                )
            )
            if not result.scalar_one_or_none():
                errors.append(f"记忆配置 '{preset.selected_memory}' 不存在或未激活")
        
        # 如果有错误，抛出异常
        if errors:
            error_msg = f"预设方案 '{preset.preset_id}' 资源校验失败:\n" + "\n".join(f"  - {e}" for e in errors)
            self.logger.error(f"[PresetEngine] {error_msg}")
            raise ValueError(error_msg)
        
        self.logger.info(f"[PresetEngine] 资源校验通过: {preset.preset_id}")
    
    async def get_model(self, model_id: str) -> BaseChatModel:
        """获取/创建模型实例（带缓存）"""
        if model_id in self._model_cache:
            return self._model_cache[model_id]
        
        result = await self.db.execute(
            select(ModelConfig).where(ModelConfig.model_id == model_id)
        )
        model_config = result.scalar_one_or_none()
        
        if not model_config:
            raise ValueError(f"模型 '{model_id}' 不存在")
        
        model = self._create_model_instance(model_config)
        self._model_cache[model_id] = model
        
        return model
    
    def _create_model_instance(self, config: ModelConfig) -> BaseChatModel:
        """根据配置创建模型实例"""
        provider = config.provider
        # model_name 可能是列表或字符串，取第一个或直接使用
        model_name = config.model_name
        if isinstance(model_name, list):
            model_name = model_name[0] if model_name else ""
        params = config.default_params or {}
        
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_name,
                api_key=config.api_key,
                base_url=config.api_base,
                **params
            )
        elif provider == "deepseek":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_name,
                api_key=config.api_key,
                base_url=config.api_base or "https://api.deepseek.com/v1",
                **params
            )
        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=model_name,
                base_url=config.api_base or "http://localhost:11434",
                **params
            )
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=model_name,
                api_key=config.api_key,
                **params
            )
        elif provider == "zhipu":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_name,
                api_key=config.api_key,
                base_url=config.api_base or "https://open.bigmodel.cn/api/paas/v4",
                **params
            )
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
    
    async def _get_system_prompt(self, preset: Preset) -> str:
        """获取系统提示词"""
        if not preset.selected_prompt:
            return ""
        
        result = await self.db.execute(
            select(PromptConfig).where(PromptConfig.prompt_id == preset.selected_prompt)
        )
        prompt_config = result.scalar_one_or_none()
        
        if prompt_config:
            return prompt_config.system_prompt
        
        return ""
    
    def _create_agent_node(self, model: BaseChatModel, system_prompt: str, enable_tools: bool = False):
        """创建 Agent 节点"""
        # 构建提示词模板
        messages = [("system", system_prompt)] if system_prompt else []
        messages.append(("placeholder", "{messages}"))
        
        prompt = ChatPromptTemplate.from_messages(messages)
        
        # LCEL 链: prompt | model
        chain = prompt | model
        
        async def _agent_node(state: AgentState) -> AgentState:
            """Agent 决策节点"""
            try:
                # 增加步骤计数
                step_count = state.get("step_count", 0) + 1
                
                # 调用模型
                response = await chain.ainvoke({"messages": state["messages"]})
                
                # 添加 AI 消息到历史
                new_messages = list(state["messages"]) + [response]
                
                return AgentState(
                    messages=new_messages,
                    input=state["input"],
                    preset_id=state["preset_id"],
                    session_id=state.get("session_id"),
                    retrieved_context=state.get("retrieved_context"),
                    needs_retrieval=state.get("needs_retrieval", False),
                    tool_results=state.get("tool_results"),
                    needs_tool_call=False,  # 由条件边判断
                    step_count=step_count,
                    max_steps=state.get("max_steps", 10),
                    overrides=state.get("overrides"),
                    error=None
                )
            except Exception as e:
                return AgentState(
                    messages=state["messages"],
                    input=state["input"],
                    preset_id=state["preset_id"],
                    session_id=state.get("session_id"),
                    retrieved_context=state.get("retrieved_context"),
                    needs_retrieval=state.get("needs_retrieval", False),
                    tool_results=state.get("tool_results"),
                    needs_tool_call=False,
                    step_count=state.get("step_count", 0) + 1,
                    max_steps=state.get("max_steps", 10),
                    overrides=state.get("overrides"),
                    error=str(e)
                )
        
        return _agent_node
    
    def _create_retrieval_node(self, rag_engine: RAGEngine, knowledge_base_ids: List[str]):
        """创建检索节点"""
        async def _retrieval_node(state: AgentState) -> AgentState:
            """RAG 检索节点"""
            try:
                # 执行检索
                documents = await rag_engine.retrieve(
                    query=state["input"],
                    knowledge_base_ids=knowledge_base_ids,
                    top_k=5
                )
                
                # 格式化上下文
                from app.core.state_types import format_retrieved_context
                context = format_retrieved_context(documents)
                
                # 如果有检索结果，添加到系统提示词
                if context:
                    # 找到系统消息并更新
                    new_messages = []
                    context_added = False
                    
                    for msg in state["messages"]:
                        if isinstance(msg, SystemMessage) and not context_added:
                            new_content = f"{msg.content}\n\n基于以下参考信息回答问题：\n\n{context}"
                            new_messages.append(SystemMessage(content=new_content))
                            context_added = True
                        else:
                            new_messages.append(msg)
                    
                    return AgentState(
                        messages=new_messages,
                        input=state["input"],
                        preset_id=state["preset_id"],
                        session_id=state.get("session_id"),
                        retrieved_context=context,
                        needs_retrieval=True,
                        tool_results=state.get("tool_results"),
                        needs_tool_call=state.get("needs_tool_call", False),
                        step_count=state.get("step_count", 0),
                        max_steps=state.get("max_steps", 10),
                        overrides=state.get("overrides"),
                        error=state.get("error")
                    )
                
                return state
                
            except Exception as e:
                return AgentState(
                    messages=state["messages"],
                    input=state["input"],
                    preset_id=state["preset_id"],
                    session_id=state.get("session_id"),
                    retrieved_context=None,
                    needs_retrieval=False,
                    tool_results=state.get("tool_results"),
                    needs_tool_call=state.get("needs_tool_call", False),
                    step_count=state.get("step_count", 0),
                    max_steps=state.get("max_steps", 10),
                    overrides=state.get("overrides"),
                    error=str(e)
                )
        
        return _retrieval_node
    
    async def build_graph(
        self,
        preset: Preset,
        enable_rag: bool = True,
        enable_tools: bool = True
    ) -> StateGraph:
        """
        构建 LangGraph StateGraph
        
        工作流：
        1. retrieval (可选) -> 2. agent -> 3. 条件判断 -> tools/agent/end
        
        Args:
            preset: 预设方案
            enable_rag: 是否启用 RAG
            enable_tools: 是否启用工具调用
            
        Returns:
            StateGraph: 编译后的状态图
        """
        # 获取模型和提示词
        model = await self.get_model(preset.selected_model)
        system_prompt = await self._get_system_prompt(preset)
        
        # 创建图构建器
        workflow = StateGraph(AgentState)
        
        # 添加检索节点（如果需要）
        if enable_rag and preset.selected_knowledge_bases:
            rag_engine = RAGEngine(self.db)
            retrieval_node = self._create_retrieval_node(
                rag_engine,
                preset.selected_knowledge_bases
            )
            workflow.add_node("retrieval", retrieval_node)
        
        # 添加 Agent 节点
        agent_node = self._create_agent_node(model, system_prompt, enable_tools)
        workflow.add_node("agent", agent_node)
        
        # 添加工具节点（如果需要）
        if enable_tools and preset.selected_plugins:
            tool_engine = ToolEngine(self.db, preset.selected_plugins)
            tool_node = tool_engine.create_tool_node()
            if tool_node:
                workflow.add_node("tools", tool_node)
        
        # 设置入口点
        if enable_rag and preset.selected_knowledge_bases:
            workflow.set_entry_point("retrieval")
            workflow.add_edge("retrieval", "agent")
        else:
            workflow.set_entry_point("agent")
        
        # 添加条件边：从 agent 到 tools 或 end
        if enable_tools and preset.selected_plugins and tool_node:
            workflow.add_conditional_edges(
                "agent",
                should_continue_to_tools,
                {
                    "tools": "tools",
                    "agent": END  # 如果没有工具调用，直接结束
                }
            )
            # 工具执行后返回 agent
            workflow.add_edge("tools", "agent")
        else:
            # 没有工具，直接结束
            workflow.add_edge("agent", END)
        
        # 编译图
        # 使用内存检查点器支持循环
        memory = MemorySaver()
        graph = workflow.compile(checkpointer=memory)
        
        return graph
    
    async def chat(
        self,
        preset_id: str,
        message: str,
        session_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        enable_tools: bool = True,
        enable_rag: bool = True,
        enable_memory: bool = True
    ) -> AsyncIterator[str]:
        """
        执行对话
        
        Args:
            preset_id: 预设方案ID
            message: 用户消息
            session_id: 会话ID
            history: 历史消息列表
            stream: 是否流式输出
            enable_tools: 是否启用工具
            enable_rag: 是否启用 RAG
            enable_memory: 是否启用记忆
            
        Yields:
            str: AI 回复内容
        """
        # 加载预设
        preset = await self.load_preset(preset_id)
        
        # 校验所有引用的资源
        await self.validate_preset_resources(preset)
        
        # 获取系统提示词
        system_prompt = await self._get_system_prompt(preset)
        
        # 获取记忆配置
        memory_config = None
        if enable_memory and preset.selected_memory:
            memory_config = await self._get_memory_config(preset)
        
        # 将长期记忆注入系统提示词
        if enable_memory and session_id and preset.selected_memory:
            memory_service = MemoryService(self.db)
            system_prompt = await memory_service.add_memory_to_prompt(
                session_id=session_id,
                memory_id=preset.selected_memory,
                base_prompt=system_prompt
            )
            self.logger.info(f"[PresetEngine] 已将长期记忆注入系统提示词")
        
        # 创建初始状态
        state = create_initial_state(
            input_message=message,
            preset_id=preset_id,
            session_id=session_id,
            system_prompt=system_prompt,
            overrides=preset.overrides
        )
        
        # 加载历史消息（不包括当前消息）
        history_messages = []
        if enable_memory and session_id:
            # 优先从记忆系统加载
            self.logger.info(f"[PresetEngine] 加载记忆历史：session={session_id}, enable_memory={enable_memory}")
            history_messages = await self._load_conversation_history(
                session_id, 
                memory_config
            )
            self.logger.info(f"[PresetEngine] 加载到 {len(history_messages)} 条历史消息")
        elif history:
            # 使用传入的历史消息
            history_messages = history
        
        # 过滤掉最后一条用户消息（如果与当前消息相同，说明已经保存到数据库）
        # 这样可以避免重复添加当前消息
        if history_messages:
            # 检查最后一条是否是当前这条消息
            last_msg = history_messages[-1]
            if last_msg.get("role") == "user" and last_msg.get("content") == message:
                # 去掉最后一条，避免重复
                history_messages = history_messages[:-1]
                self.logger.info(f"[PresetEngine] 移除重复的当前消息")
        
        # 添加历史消息到状态
        for msg in history_messages:
            if msg.get("role") == "user":
                state["messages"].append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                state["messages"].append(AIMessage(content=msg.get("content", "")))
        
        if history_messages:
            self.logger.info(f"[PresetEngine] 已添加 {len(history_messages)} 条历史消息到上下文")
        
        # 添加当前用户消息
        state["messages"].append(HumanMessage(content=message))
        
        # 构建图
        graph = await self.build_graph(
            preset,
            enable_rag=enable_rag,
            enable_tools=enable_tools
        )
        
        # 执行图配置
        config = {"configurable": {"thread_id": session_id or "default"}}
        
        # 添加 LangSmith 追踪元数据
        metadata = {
            "preset_id": preset_id,
            "session_id": session_id,
            "enable_rag": enable_rag,
            "enable_tools": enable_tools,
            "enable_memory": enable_memory,
            "model_id": preset.selected_model,
        }
        
        # 如果启用了 LangSmith，添加追踪配置
        if os.environ.get("LANGCHAIN_TRACING_V2") == "true":
            config["metadata"] = metadata
            self.logger.info(f"[PresetEngine] LangSmith 追踪已启用: {metadata}")
        
        try:
            self.logger.info(f"[PresetEngine] 开始执行对话：preset={preset_id}, session={session_id}")
            
            if stream:
                # 使用 LangGraph 的 stream_events API 流式输出 token
                async for event in graph.astream_events(state, config, version="v2"):
                    # 处理 LLM/ChatModel 的 token 事件
                    if event["event"] in ["on_llm_stream", "on_chat_model_stream"]:
                        chunk = event.get("data", {}).get("chunk")
                        if chunk:
                            content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                            if content:
                                yield content
                self.logger.info(f"[PresetEngine] 流式输出结束")
            else:
                result = await graph.ainvoke(state, config)
                # 获取最后一条 AI 消息
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage):
                        content = msg.content
                        self.logger.info(f"[PresetEngine] 对话完成，生成 {len(content)} 字符")
                        yield msg.content
                        break
                        
        except Exception as e:
            error_msg = f"[对话执行错误：{str(e)}]"
            self.logger.error(f"[PresetEngine] 对话执行失败：{e}", exc_info=True)
            yield error_msg
    
    async def get_preset_detail(self, preset_id: str) -> Dict[str, Any]:
        """获取预设方案详情"""
        preset = await self.load_preset(preset_id)
        
        # 获取工具信息
        tool_engine = ToolEngine(self.db, preset.selected_plugins or [])
        
        tools_info = []
        for tool in tool_engine.get_tools():
            tools_info.append({
                "name": tool.name,
                "description": tool.description
            })
        
        return {
            "preset_id": preset.preset_id,
            "preset_name": preset.preset_name,
            "description": preset.description,
            "selected_model": preset.selected_model,
            "selected_prompt": preset.selected_prompt,
            "selected_memory": preset.selected_memory,
            "selected_plugins": preset.selected_plugins,
            "selected_knowledge_bases": preset.selected_knowledge_bases,
            "is_default": preset.is_default,
            "is_active": preset.is_active,
            "available_tools": tools_info
        }
