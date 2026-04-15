"""
内置工具插件

整合所有内置工具为一个插件，减少工具调用开销
source: builtin
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from app.plugins.base import BasePlugin, PluginMetadata, PluginResult

BEIJING_TZ = timezone(timedelta(hours=8))


class BuiltinToolsPlugin(BasePlugin):
    """
    内置工具插件

    提供查询北京时间功能
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="builtin_tools",
            description="内置工具箱：查询北京时间",
            version="2.0.0",
            author="HAXAtom",
            category="tool",
            icon="🧰",
            tags=["builtin", "time", "beijing"],
            source="builtin",
            config_schema={
                "type": "object",
                "properties": {}
            },
            default_config={}
        )

    async def execute(self, params: Dict[str, Any]) -> PluginResult:
        """
        执行内置工具

        Args:
            params: 包含 tool 和对应参数的字典
                   {"tool": "time"}
        """
        tool = params.get("tool", "").lower()

        if tool == "time":
            return self._get_time()
        else:
            return PluginResult.error(
                error="unknown_tool",
                message=f"未知工具: {tool}，支持的工具: time"
            )

    def _get_time(self) -> PluginResult:
        """获取当前时间（北京时间）"""
        now = datetime.now(BEIJING_TZ)
        weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday = weekday_names[now.weekday()]

        data = {
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "weekday": weekday,
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "timestamp": int(now.timestamp())
        }

        return PluginResult.ok(data=data, message=f"当前时间：{data['datetime']} {weekday}")

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证参数"""
        tool = params.get("tool", "").lower()

        if tool not in ["time"]:
            return False, f"未知工具: {tool}，支持的工具: time"

        return True, None