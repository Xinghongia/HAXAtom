"""
内置工具插件

整合所有内置工具为一个插件，减少工具调用开销
source: builtin
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

from app.plugins.base import BasePlugin, PluginMetadata, PluginResult


class BuiltinToolsPlugin(BasePlugin):
    """
    内置工具插件

    整合 time、search 功能，减少 AI 工具调用次数
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="builtin_tools",
            description="内置工具箱：查询时间/日期(search by keyword)，搜索网络信息(web search)",
            version="1.0.0",
            author="HAXAtom",
            category="tool",
            icon="🧰",
            tags=["builtin", "time", "search", "web"],
            source="builtin",
            config_schema={
                "type": "object",
                "properties": {
                    "search_engine": {
                        "type": "string",
                        "enum": ["baidu", "google", "bing"],
                        "default": "baidu",
                        "description": "搜索引擎"
                    }
                }
            },
            default_config={
                "search_engine": "baidu"
            }
        )

    async def execute(self, params: Dict[str, Any]) -> PluginResult:
        """
        执行内置工具

        Args:
            params: 包含 tool 和对应参数的字典
                   {"tool": "time"} 或 {"tool": "search", "query": "..."}
        """
        tool = params.get("tool", "").lower()

        if tool == "time":
            return self._get_time()
        elif tool == "search":
            query = params.get("query", "")
            return await self._search_web(query)
        else:
            return PluginResult.error(
                error="unknown_tool",
                message=f"未知工具: {tool}，支持的工具: time, search"
            )

    def _get_time(self) -> PluginResult:
        """获取当前时间"""
        now = datetime.now()
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

    async def _search_web(self, query: str) -> PluginResult:
        """
        搜索网络

        Args:
            query: 搜索关键词
        """
        if not query or not query.strip():
            return PluginResult.error(error="empty_query", message="搜索关键词不能为空")

        query = query.strip()

        search_engine = self.get_config("search_engine", "baidu")

        try:
            if search_engine == "baidu":
                results = await self._search_baidu(query)
            elif search_engine == "bing":
                results = await self._search_bing(query)
            elif search_engine == "google":
                results = await self._search_google(query)
            else:
                results = await self._search_baidu(query)

            if not results:
                return PluginResult.ok(data=[], message=f"未找到关于「{query}」的相关结果")

            return PluginResult.ok(
                data=results,
                message=f"找到 {len(results)} 条关于「{query}」的相关结果"
            )

        except Exception as e:
            return PluginResult.error(error="search_failed", message=f"搜索失败: {str(e)}")

    async def _search_baidu(self, query: str) -> list:
        """百度搜索"""
        url = f"https://www.baidu.com/s?wd={requests.utils.quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for item in soup.select(".result")[:10]:
            title_elem = item.select_one("h3 a")
            abstract_elem = item.select_one(".c-abstract, .content-right_8Zs40")

            if title_elem:
                title = title_elem.get_text(strip=True)
                link = title_elem.get("href", "")
                abstract = abstract_elem.get_text(strip=True) if abstract_elem else ""

                results.append({
                    "title": title,
                    "url": link,
                    "abstract": abstract[:200] + "..." if len(abstract) > 200 else abstract,
                    "source": "baidu"
                })

        return results

    async def _search_bing(self, query: str) -> list:
        """必应搜索"""
        url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for item in soup.select(".b_algo")[:10]:
            title_elem = item.select_one("h2 a")
            abstract_elem = item.select_one(".b_caption p")

            if title_elem:
                title = title_elem.get_text(strip=True)
                link = title_elem.get("href", "")
                abstract = abstract_elem.get_text(strip=True) if abstract_elem else ""

                results.append({
                    "title": title,
                    "url": link,
                    "abstract": abstract[:200] + "..." if len(abstract) > 200 else abstract,
                    "source": "bing"
                })

        return results

    async def _search_google(self, query: str) -> list:
        """Google搜索（简单实现）"""
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for item in soup.select(".g")[:10]:
            title_elem = item.select_one("h3")
            link_elem = item.select_one("a")
            abstract_elem = item.select_one(".IsZvec")

            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                link = link_elem.get("href", "")
                abstract = abstract_elem.get_text(strip=True) if abstract_elem else ""

                results.append({
                    "title": title,
                    "url": link,
                    "abstract": abstract[:200] + "..." if len(abstract) > 200 else abstract,
                    "source": "google"
                })

        return results

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证参数"""
        tool = params.get("tool", "").lower()

        if tool not in ["time", "search"]:
            return False, f"未知工具: {tool}，支持的工具: time, search"

        if tool == "search":
            query = params.get("query", "")
            if not query or not query.strip():
                return False, "搜索关键词不能为空"

        return True, None
