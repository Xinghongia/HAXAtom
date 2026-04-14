"""
OneBot v11 适配器测试脚本

测试消息解析、格式化回复等功能
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.channels.adapters.onebot11 import OneBot11Adapter


def test_parse_private_message():
    """测试解析私聊消息"""
    adapter = OneBot11Adapter()

    raw_message = {
        "post_type": "message",
        "message_type": "private",
        "sub_type": "friend",
        "user_id": 123456789,
        "message": [
            {"type": "text", "data": {"text": "你好"}}
        ],
        "raw_message": "你好",
        "message_id": 12345,
        "sender": {"user_id": 123456789, "nickname": "测试用户"},
        "time": 1234567890
    }

    msg = adapter.parse_message(raw_message)

    assert msg.session_id == "onebot11_private_123456789", f"session_id 错误: {msg.session_id}"
    assert msg.channel_type == "onebot11"
    assert msg.user_id == "123456789"
    assert msg.content == "你好"
    assert msg.role == "user"
    assert msg.message_id == "12345"

    print("[PASS] 私聊消息解析测试通过")


def test_parse_group_message():
    """测试解析群聊消息"""
    adapter = OneBot11Adapter()

    raw_message = {
        "post_type": "message",
        "message_type": "group",
        "sub_type": "normal",
        "user_id": 987654321,
        "group_id": 111222333,
        "message": [
            {"type": "text", "data": {"text": "Hello"}}
        ],
        "raw_message": "Hello",
        "message_id": 54321,
        "sender": {"user_id": 987654321, "nickname": "群友", "card": "群友"},
        "time": 1234567891
    }

    msg = adapter.parse_message(raw_message)

    assert msg.session_id == "onebot11_group_111222333_987654321", f"session_id 错误: {msg.session_id}"
    assert msg.group_id == "111222333"
    assert msg.content == "Hello"

    print("[PASS] 群聊消息解析测试通过")


def test_parse_message_with_at():
    """测试解析带 @ 的消息"""
    adapter = OneBot11Adapter()

    raw_message = {
        "post_type": "message",
        "message_type": "group",
        "user_id": 111222333,
        "group_id": 555666777,
        "message": [
            {"type": "at", "data": {"qq": "123456"}},
            {"type": "text", "data": {"text": " 在吗？"}}
        ],
        "raw_message": "",
        "message_id": 99999,
        "time": 1234567892
    }

    msg = adapter.parse_message(raw_message)

    assert "@123456" in msg.content
    assert "在吗？" in msg.content

    print("[PASS] @消息解析测试通过")


def test_format_reply():
    """测试回复格式化"""
    adapter = OneBot11Adapter()

    reply = adapter.format_reply("这是回复内容")

    assert reply == {"message": "这是回复内容"}

    print("[PASS] 回复格式化测试通过")


def test_channel_type():
    """测试渠道类型"""
    adapter = OneBot11Adapter()

    assert adapter.channel_type == "onebot11"

    print("[PASS] 渠道类型测试通过")


async def test_async_methods():
    """测试异步方法（需要数据库连接）"""
    print("[SKIP] 异步测试跳过（需要数据库连接）")
    print("   如需测试，请先运行: poetry run python -c 'from app.db.session import init_db; asyncio.run(init_db())'")


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("  OneBot v11 适配器测试")
    print("=" * 50 + "\n")

    test_channel_type()
    test_parse_private_message()
    test_parse_group_message()
    test_parse_message_with_at()
    test_format_reply()

    print("\n" + "=" * 50)
    print("  所有同步测试通过!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
