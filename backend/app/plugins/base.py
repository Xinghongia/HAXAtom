"""
插件基类

定义插件的标准接口和元数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PluginMetadata:
    """
    插件元数据

    描述插件的基本信息
    """
    name: str  # 插件名称
    description: str  # 插件描述
    version: str = "1.0.0"  # 版本号
    author: str = "Unknown"  # 作者
    category: str = "general"  # 分类：general/tool/search/calculation等
    icon: Optional[str] = None  # 图标URL或emoji
    tags: List[str] = field(default_factory=list)  # 标签

    # 来源类型: builtin(内置) | skill(用户技能) | mcp(MCP服务) | community(社区)
    source: str = "builtin"

    # 社区插件专用字段
    homepage: Optional[str] = None  # 插件主页
    license: str = "MIT"  # 许可证
    requirements: List[str] = field(default_factory=list)  # Python 依赖

    # MCP 专用配置
    mcp_config: Optional[Dict[str, Any]] = None  # MCP 服务器配置

    # 配置信息
    config_schema: Optional[Dict[str, Any]] = None  # 配置项JSON Schema
    default_config: Dict[str, Any] = field(default_factory=dict)  # 默认配置


@dataclass
class PluginResult:
    """
    插件执行结果
    
    统一插件返回格式
    """
    success: bool  # 是否成功
    data: Any  # 返回数据
    message: str = ""  # 提示信息
    error: Optional[str] = None  # 错误信息
    
    @classmethod
    def ok(cls, data: Any, message: str = "") -> "PluginResult":
        """创建成功结果"""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error(cls, error: str, message: str = "") -> "PluginResult":
        """创建错误结果"""
        return cls(success=False, data=None, message=message, error=error)


class BasePlugin(ABC):
    """
    插件基类
    
    所有插件必须继承此类并实现抽象方法
    
    示例：
        class WeatherPlugin(BasePlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="weather",
                    description="查询天气信息",
                    version="1.0.0"
                )
            
            async def execute(self, params: Dict[str, Any]) -> PluginResult:
                city = params.get("city")
                # 查询天气逻辑...
                return PluginResult.ok(data={"temperature": 25})
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化插件
        
        Args:
            config: 插件配置
        """
        self.config = config or {}
        self._enabled = True
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """
        插件元数据
        
        Returns:
            PluginMetadata: 插件元数据对象
        """
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> PluginResult:
        """
        执行插件功能
        
        Args:
            params: 执行参数
            
        Returns:
            PluginResult: 执行结果
        """
        pass
    
    async def initialize(self) -> bool:
        """
        初始化插件（可选重写）
        
        在插件加载时调用，用于初始化资源
        
        Returns:
            bool: 初始化是否成功
        """
        return True
    
    async def shutdown(self) -> None:
        """
        关闭插件（可选重写）
        
        在插件卸载时调用，用于释放资源
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证参数（可选重写）
        
        Args:
            params: 待验证的参数
            
        Returns:
            tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        return True, None
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.config.get(key, default)
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            config: 新配置
        """
        self.config.update(config)
    
    @property
    def enabled(self) -> bool:
        """插件是否启用"""
        return self._enabled
    
    def enable(self) -> None:
        """启用插件"""
        self._enabled = True
    
    def disable(self) -> None:
        """禁用插件"""
        self._enabled = False
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.metadata.name}', enabled={self.enabled})>"
