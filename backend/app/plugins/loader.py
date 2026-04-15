"""
插件加载器

负责从文件系统或数据库加载插件
"""

import importlib
import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from app.plugins.base import BasePlugin
from app.plugins.registry import PluginRegistry


class PluginLoader:
    """
    插件加载器
    
    支持从以下位置加载插件：
    1. 内置插件（app/plugins/builtin/）
    2. 外部插件目录（可配置）
    3. 数据库中的插件配置
    
    示例：
        loader = PluginLoader()
        loader.load_builtin_plugins()
        loader.load_from_directory("/path/to/plugins")
    """
    
    def __init__(self, registry: Optional[PluginRegistry] = None):
        """
        初始化插件加载器
        
        Args:
            registry: 插件注册表，为空则使用全局注册表
        """
        self.registry = registry or PluginRegistry()
        self._loaded_plugins: List[str] = []
    
    def load_builtin_plugins(self) -> List[str]:
        """
        加载内置插件（app/plugins/builtin/）

        Returns:
            List[str]: 成功加载的插件ID列表
        """
        loaded = []

        # 内置插件目录
        builtin_dir = Path(__file__).parent / "builtin"

        if not builtin_dir.exists():
            print(f"[PluginLoader] Builtin directory not found: {builtin_dir}")
            return loaded

        # 加载 builtin 目录下的所有 Python 文件
        for file_path in builtin_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            plugin_id = self._load_from_file(file_path)
            if plugin_id:
                loaded.append(plugin_id)

        print(f"[PluginLoader] Loaded {len(loaded)} builtin plugins: {loaded}")
        return loaded

    def load_skills_plugins(self) -> List[str]:
        """
        加载用户技能插件（app/plugins/skills/）

        Returns:
            List[str]: 成功加载的插件ID列表
        """
        loaded = []

        skills_dir = Path(__file__).parent / "skills"

        if not skills_dir.exists():
            print(f"[PluginLoader] Skills directory not found: {skills_dir}")
            return loaded

        for file_path in skills_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            plugin_id = self._load_from_file(file_path)
            if plugin_id:
                loaded.append(plugin_id)

        print(f"[PluginLoader] Loaded {len(loaded)} skills plugins: {loaded}")
        return loaded

    def load_mcp_plugins(self) -> List[str]:
        """
        加载 MCP 服务插件（app/plugins/mcp/）

        Returns:
            List[str]: 成功加载的插件ID列表
        """
        loaded = []

        mcp_dir = Path(__file__).parent / "mcp"

        if not mcp_dir.exists():
            print(f"[PluginLoader] MCP directory not found: {mcp_dir}")
            return loaded

        # MCP 目录下可能有 adapters/ 子目录，跳过加载整个目录
        # 具体的 MCP 适配器应该通过 adapter.py 统一加载
        for file_path in mcp_dir.glob("*.py"):
            if file_path.name.startswith("_") or file_path.stem == "adapter":
                continue

            plugin_id = self._load_from_file(file_path)
            if plugin_id:
                loaded.append(plugin_id)

        print(f"[PluginLoader] Loaded {len(loaded)} MCP plugins: {loaded}")
        return loaded

    def load_all_plugins(self) -> Dict[str, List[str]]:
        """
        加载所有类型的插件

        Returns:
            Dict[str, List[str]]: 各类型插件加载结果
        """
        results = {
            "builtin": self.load_builtin_plugins(),
            "skill": self.load_skills_plugins(),
            "mcp": self.load_mcp_plugins(),
            "community": self.load_community_plugins(),
        }
        return results

    def load_community_plugins(self) -> List[str]:
        """
        加载社区插件（app/plugins/community/）

        Returns:
            List[str]: 成功加载的插件ID列表
        """
        loaded = []

        community_dir = Path(__file__).parent / "community"

        if not community_dir.exists():
            print(f"[PluginLoader] Community directory not found: {community_dir}")
            return loaded

        for file_path in community_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            plugin_id = self._load_from_file(file_path)
            if plugin_id:
                loaded.append(plugin_id)

        print(f"[PluginLoader] Loaded {len(loaded)} community plugins: {loaded}")
        return loaded
    
    def load_from_directory(self, directory: str) -> List[str]:
        """
        从指定目录加载插件
        
        Args:
            directory: 插件目录路径
            
        Returns:
            List[str]: 成功加载的插件ID列表
        """
        loaded = []
        plugin_dir = Path(directory)
        
        if not plugin_dir.exists():
            print(f"[PluginLoader] Directory not found: {directory}")
            return loaded
        
        # 加载目录下的所有 Python 文件
        for file_path in plugin_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            plugin_id = self._load_from_file(file_path)
            if plugin_id:
                loaded.append(plugin_id)
        
        print(f"[PluginLoader] Loaded {len(loaded)} plugins from {directory}: {loaded}")
        return loaded
    
    def load_from_module(self, module_path: str, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        从模块路径加载插件
        
        Args:
            module_path: 模块导入路径，如 "app.plugins.builtin.weather"
            config: 插件配置
            
        Returns:
            Optional[str]: 插件ID，失败返回None
        """
        try:
            # 导入模块
            module = importlib.import_module(module_path)
            
            # 查找插件类
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                print(f"[PluginLoader] No plugin class found in module: {module_path}")
                return None
            
            # 注册插件
            plugin_id = self.registry.register(plugin_class, config)
            if plugin_id:
                self._loaded_plugins.append(plugin_id)
            
            return plugin_id
            
        except Exception as e:
            print(f"[PluginLoader] Failed to load module {module_path}: {e}")
            return None
    
    def _load_from_file(self, file_path: Path, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        从文件加载插件
        
        Args:
            file_path: 插件文件路径
            config: 插件配置
            
        Returns:
            Optional[str]: 插件ID，失败返回None
        """
        try:
            # 动态导入模块
            module_name = f"_plugin_{file_path.stem}_{id(self)}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            
            if not spec or not spec.loader:
                print(f"[PluginLoader] Cannot load spec from: {file_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                print(f"[PluginLoader] No plugin class found in: {file_path}")
                return None
            
            # 注册插件
            plugin_id = self.registry.register(plugin_class, config)
            if plugin_id:
                self._loaded_plugins.append(plugin_id)
            
            return plugin_id
            
        except Exception as e:
            print(f"[PluginLoader] Failed to load file {file_path}: {e}")
            return None
    
    def _find_plugin_class(self, module) -> Optional[Type[BasePlugin]]:
        """
        在模块中查找插件类
        
        Args:
            module: 模块对象
            
        Returns:
            Optional[Type[BasePlugin]]: 插件类，未找到返回None
        """
        for name, obj in inspect.getmembers(module):
            # 跳过私有成员和导入的类
            if name.startswith("_"):
                continue
            
            # 检查是否是类且继承 BasePlugin
            if inspect.isclass(obj) and issubclass(obj, BasePlugin) and obj is not BasePlugin:
                return obj
        
        return None
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否成功
        """
        if plugin_id in self._loaded_plugins:
            self._loaded_plugins.remove(plugin_id)
        
        return self.registry.unregister(plugin_id)
    
    def get_loaded_plugins(self) -> List[str]:
        """
        获取已加载的插件列表
        
        Returns:
            List[str]: 插件ID列表
        """
        return self._loaded_plugins.copy()
    
    def reload_plugin(self, plugin_id: str) -> Optional[str]:
        """
        重新加载插件（开发调试用）
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[str]: 新插件ID，失败返回None
        """
        # 获取原插件配置
        plugin = self.registry.get(plugin_id)
        if not plugin:
            print(f"[PluginLoader] Plugin not found: {plugin_id}")
            return None
        
        config = plugin.config
        
        # 卸载原插件
        self.unload_plugin(plugin_id)
        
        # TODO: 重新加载（需要记录原文件路径）
        print(f"[PluginLoader] Reload not fully implemented yet")
        return None
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        初始化所有已加载的插件
        
        Returns:
            Dict[str, bool]: 各插件初始化结果
        """
        return await self.registry.initialize_all()
    
    async def shutdown_all(self) -> None:
        """关闭所有已加载的插件"""
        await self.registry.shutdown_all()


# 全局加载器实例
loader = PluginLoader()
