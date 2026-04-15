"""
插件注册表

管理插件的注册、查询和生命周期
"""

from typing import Any, Dict, List, Optional, Type

from app.plugins.base import BasePlugin, PluginMetadata


class PluginRegistry:
    """
    插件注册表
    
    单例模式管理所有插件实例
    
    示例：
        registry = PluginRegistry()
        registry.register(WeatherPlugin)
        plugin = registry.get("weather")
        result = await plugin.execute({"city": "北京"})
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins: Dict[str, BasePlugin] = {}
            cls._instance._plugin_classes: Dict[str, Type[BasePlugin]] = {}
        return cls._instance
    
    def register(
        self,
        plugin_class: Type[BasePlugin],
        config: Optional[Dict[str, Any]] = None,
        plugin_id: Optional[str] = None
    ) -> bool:
        """
        注册插件
        
        Args:
            plugin_class: 插件类（继承BasePlugin）
            config: 插件配置
            plugin_id: 自定义插件ID，为空则使用metadata.name
            
        Returns:
            bool: 是否注册成功
        """
        try:
            # 创建实例获取metadata
            temp_instance = plugin_class()
            metadata = temp_instance.metadata
            
            plugin_id = plugin_id or metadata.name
            
            # 检查是否已注册
            if plugin_id in self._plugins:
                print(f"[PluginRegistry] Plugin '{plugin_id}' already registered")
                return False
            
            # 创建正式实例
            instance = plugin_class(config=config)
            
            # 存储
            self._plugins[plugin_id] = instance
            self._plugin_classes[plugin_id] = plugin_class
            
            print(f"[PluginRegistry] Registered plugin: {plugin_id} ({metadata.description})")
            return True
            
        except Exception as e:
            print(f"[PluginRegistry] Failed to register plugin: {e}")
            return False
    
    def unregister(self, plugin_id: str) -> bool:
        """
        注销插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否注销成功
        """
        if plugin_id not in self._plugins:
            return False
        
        # 调用关闭方法
        plugin = self._plugins[plugin_id]
        try:
            import asyncio
            asyncio.create_task(plugin.shutdown())
        except:
            pass
        
        # 移除
        del self._plugins[plugin_id]
        del self._plugin_classes[plugin_id]
        
        print(f"[PluginRegistry] Unregistered plugin: {plugin_id}")
        return True
    
    def get(self, plugin_id: str) -> Optional[BasePlugin]:
        """
        获取插件实例
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[BasePlugin]: 插件实例，不存在返回None
        """
        return self._plugins.get(plugin_id)
    
    def get_metadata(self, plugin_id: str) -> Optional[PluginMetadata]:
        """
        获取插件元数据
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[PluginMetadata]: 插件元数据
        """
        plugin = self.get(plugin_id)
        if plugin:
            return plugin.metadata
        return None
    
    def list_plugins(self) -> List[str]:
        """
        获取所有已注册插件ID列表
        
        Returns:
            List[str]: 插件ID列表
        """
        return list(self._plugins.keys())
    
    def list_enabled(self) -> List[str]:
        """
        获取所有启用的插件ID列表
        
        Returns:
            List[str]: 启用的插件ID列表
        """
        return [
            plugin_id for plugin_id, plugin in self._plugins.items()
            if plugin.enabled
        ]
    
    def get_all_metadata(self) -> Dict[str, PluginMetadata]:
        """
        获取所有插件元数据

        Returns:
            Dict[str, PluginMetadata]: 插件ID到元数据的映射
        """
        return {
            plugin_id: plugin.metadata
            for plugin_id, plugin in self._plugins.items()
        }

    def list_by_source(self, source: str) -> List[str]:
        """
        按来源类型获取插件列表

        Args:
            source: 来源类型 (builtin | skill | mcp | community)

        Returns:
            List[str]: 该来源的所有插件ID
        """
        return [
            plugin_id
            for plugin_id, plugin in self._plugins.items()
            if plugin.metadata.source == source
        ]

    def list_by_category(self, category: str) -> List[str]:
        """
        按功能类别获取插件列表

        Args:
            category: 功能类别 (tool | search | calculation | general)

        Returns:
            List[str]: 该类别的所有插件ID
        """
        return [
            plugin_id
            for plugin_id, plugin in self._plugins.items()
            if plugin.metadata.category == category
        ]

    def get_by_source(self, source: str) -> Dict[str, BasePlugin]:
        """
        按来源类型获取插件实例

        Args:
            source: 来源类型 (builtin | skill | mcp | community)

        Returns:
            Dict[str, BasePlugin]: 该来源的所有插件实例
        """
        return {
            plugin_id: plugin
            for plugin_id, plugin in self._plugins.items()
            if plugin.metadata.source == source
        }

    def get_all_sources(self) -> List[str]:
        """
        获取所有来源类型

        Returns:
            List[str]: 来源类型列表
        """
        sources = set()
        for plugin in self._plugins.values():
            sources.add(plugin.metadata.source)
        return sorted(list(sources))
    
    def enable(self, plugin_id: str) -> bool:
        """
        启用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否成功
        """
        plugin = self.get(plugin_id)
        if plugin:
            plugin.enable()
            return True
        return False
    
    def disable(self, plugin_id: str) -> bool:
        """
        禁用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否成功
        """
        plugin = self.get(plugin_id)
        if plugin:
            plugin.disable()
            return True
        return False
    
    def is_registered(self, plugin_id: str) -> bool:
        """
        检查插件是否已注册
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否已注册
        """
        return plugin_id in self._plugins
    
    def clear(self) -> None:
        """清空所有插件"""
        self._plugins.clear()
        self._plugin_classes.clear()
        print("[PluginRegistry] All plugins cleared")
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        初始化所有插件
        
        Returns:
            Dict[str, bool]: 各插件初始化结果
        """
        results = {}
        for plugin_id, plugin in self._plugins.items():
            try:
                success = await plugin.initialize()
                results[plugin_id] = success
                if not success:
                    print(f"[PluginRegistry] Failed to initialize plugin: {plugin_id}")
            except Exception as e:
                results[plugin_id] = False
                print(f"[PluginRegistry] Error initializing plugin {plugin_id}: {e}")
        return results
    
    async def shutdown_all(self) -> None:
        """关闭所有插件"""
        for plugin_id, plugin in self._plugins.items():
            try:
                await plugin.shutdown()
                print(f"[PluginRegistry] Shutdown plugin: {plugin_id}")
            except Exception as e:
                print(f"[PluginRegistry] Error shutting down plugin {plugin_id}: {e}")


# 全局注册表实例
registry = PluginRegistry()
