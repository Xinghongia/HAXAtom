"""测试内置工具是否正常工作"""
import asyncio
import sys
sys.path.insert(0, '.')

# 先加载插件
from app.plugins.loader import PluginLoader
loader = PluginLoader()
loaded = loader.load_builtin_plugins()
print(f"[PLUGIN] Loaded: {loaded}")

from app.plugins import registry
from app.plugins.tool_adapter import create_tool_from_plugin, get_tools_for_preset
from app.plugins.builtin.builtin_tools import BuiltinToolsPlugin


def test_plugin_registry():
    """测试插件注册"""
    print("=" * 50)
    print("1. 测试插件注册")
    print("=" * 50)

    all_plugins = registry.list_plugins()
    enabled_plugins = registry.list_enabled()

    print(f"所有插件: {all_plugins}")
    print(f"启用插件: {enabled_plugins}")

    if "builtin_tools" not in all_plugins:
        print("❌ builtin_tools 未注册!")
        return False

    if "builtin_tools" not in enabled_plugins:
        print("❌ builtin_tools 未启用!")
        return False

    print("✅ builtin_tools 已注册并启用")
    return True


def test_plugin_instance():
    """测试插件实例"""
    print("\n" + "=" * 50)
    print("2. 测试插件实例")
    print("=" * 50)

    plugin = registry.get("builtin_tools")
    if not plugin:
        print("❌ 无法获取 builtin_tools 插件")
        return False

    print(f"插件类: {plugin.__class__.__name__}")
    print(f"插件名称: {plugin.metadata.name}")
    print(f"插件描述: {plugin.metadata.description}")
    print(f"插件启用: {plugin.enabled}")

    print("✅ 插件实例正常")
    return True


def test_tool_conversion():
    """测试工具转换"""
    print("\n" + "=" * 50)
    print("3. 测试工具转换")
    print("=" * 50)

    tool = create_tool_from_plugin("builtin_tools")
    if not tool:
        print("❌ 无法转换 builtin_tools 为 LangChain Tool")
        return False

    print(f"Tool 名称: {tool.name}")
    print(f"Tool 描述: {tool.description}")
    print(f"Tool 参数Schema: {tool.args_schema}")

    print("✅ 工具转换正常")
    return True


def test_get_tools_for_preset():
    """测试 get_tools_for_preset"""
    print("\n" + "=" * 50)
    print("4. 测试 get_tools_for_preset")
    print("=" * 50)

    tools = get_tools_for_preset(["builtin_tools"])
    print(f"获取到的工具数量: {len(tools)}")

    if not tools:
        print("❌ get_tools_for_preset 返回空列表")
        return False

    for t in tools:
        print(f"  - {t.name}: {t.description[:50]}...")

    print("✅ get_tools_for_preset 正常")
    return True


async def test_tool_execution():
    """测试工具执行"""
    print("\n" + "=" * 50)
    print("5. 测试工具执行 (time)")
    print("=" * 50)

    plugin = registry.get("builtin_tools")
    if not plugin:
        print("❌ 无法获取插件")
        return False

    result = await plugin.execute({"tool": "time"})
    print(f"执行结果: {result}")

    if result.success:
        print("✅ time 工具执行成功")
        print(f"  数据: {result.data}")
    else:
        print(f"❌ time 工具执行失败: {result.message}")

    return result.success


async def test_search_execution():
    """测试搜索执行"""
    print("\n" + "=" * 50)
    print("6. 测试工具执行 (search)")
    print("=" * 50)

    plugin = registry.get("builtin_tools")
    if not plugin:
        print("❌ 无法获取插件")
        return False

    result = await plugin.execute({"tool": "search", "query": "Python 教程"})
    print(f"执行结果: {result}")

    if result.success:
        print("✅ search 工具执行成功")
        print(f"  找到 {len(result.data)} 条结果")
    else:
        print(f"❌ search 工具执行失败: {result.message}")

    return result.success


async def main():
    """运行所有测试"""
    print("\n🔍 HAXAtom 内置工具测试\n")

    tests = [
        test_plugin_registry,
        test_plugin_instance,
        test_tool_conversion,
        test_get_tools_for_preset,
        test_tool_execution,
        test_search_execution,
    ]

    results = []
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试出错: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("🎉 所有测试通过!")
    else:
        print("⚠️ 部分测试失败")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(main())
