# QQ 机器人实现文档

## 一、概述

HAXAtom 通过 OneBot v11 协议与 QQ 机器人实现集成，采用**反向 WebSocket**架构，HAXAtom 作为服务端，NapCat（QQ 协议客户端）作为客户端主动连接。

## 二、架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                         HAXAtom                                  │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │  Web 层     │    │  交互层       │    │  核心引擎层      │    │
│  │  FastAPI    │    │  ChannelSvc  │    │  PresetEngine   │    │
│  │  :8000      │    │  ┌────────┐ │    │                 │    │
│  └─────────────┘    │  │OneBot11│ │    │  RAG / Tools    │    │
│                      │  │Adapter │ │    │  Memory         │    │
│                      │  └────────┘ │    └─────────────────┘    │
│                      │    :6199    │                             │
└──────────────────────┼────────────┼────────────────────────────┘
                       │   反向WS   │
                       │  ws://... │
                       ▼            ▼
              ┌─────────────────────────┐
              │       NapCat            │
              │   (QQ 协议客户端)        │
              │                         │
              │   接收 QQ 消息           │
              │   发送 QQ 消息           │
              └─────────────────────────┘
```

## 三、数据库模型

### 3.1 Bot 表
```python
class Bot(Base):
    __tablename__ = "bots"

    bot_id: str          # 机器人唯一标识
    bot_name: str        # 机器人名称
    channel_type: str    # 渠道类型 (onebot11 / feishu / discord ...)
    preset_id: str       # 关联的预设方案 ID
    is_active: bool      # 是否启用
    created_at: datetime
    updated_at: datetime
```

### 3.2 OneBot11Config 表
```python
class OneBot11Config(Base):
    __tablename__ = "onebot11_configs"

    bot_id: str          # 关联的 Bot ID
    listen_host: str     # 监听地址 (默认 0.0.0.0)
    listen_port: int     # 监听端口 (默认 6199)
    token: Optional[str] # 鉴权 Token
    message_post_format: str  # 消息格式 (array)
    self_message: bool   # 是否接收自己消息
    extra_config: Optional[Dict]  # 额外配置
    is_active: bool
```

## 四、核心组件

### 4.1 OneBot11Adapter
路径: `backend/app/channels/adapters/onebot11.py`

**职责:**
- 作为反向 WebSocket 服务端，等待 NapCat 连接
- 解析 OneBot v11 协议消息
- 转发消息到 ChannelService

**关键代码:**
```python
class OneBot11Adapter(ChannelAdapter):
    def __init__(self):
        self.bot = None
        self._message_handler = None
        self._server_task = None

    async def start_server(self, host, port, token):
        self.bot = CQHttp(
            access_token=token,
            enable_http_post=False,
            enable_websocket_reverse=True,
        )

        @self.bot.on("message")
        async def handle_message(event):
            channel_msg = self.parse_message(event)
            if self._message_handler:
                await self._message_handler(channel_msg)

        self._server_task = asyncio.create_task(
            self.bot.run_task(host=host, port=port)
        )
```

### 4.2 ChannelService
路径: `backend/app/channels/service.py`

**职责:**
- 管理所有渠道适配器
- 路由消息到 PresetEngine
- 处理对话历史

**消息处理流程:**
```
接收消息 → 查找 Bot 配置 → 保存用户消息 → 调用 PresetEngine → 保存 AI 回复 → 发送回复
```

## 五、初始化流程

### 5.1 默认机器人
启动时自动创建默认机器人：
```python
DEFAULT_BOTS = [
    {
        "bot_id": "default_qq_bot",
        "bot_name": "默认QQ机器人",
        "channel_type": "onebot11",
        "preset_id": "default_chat",
        "is_active": True
    }
]

DEFAULT_ONEBOT11_CONFIGS = [
    {
        "bot_id": "default_qq_bot",
        "listen_host": "0.0.0.0",
        "listen_port": 6199,
        "token": None,
        "message_post_format": "array",
        "self_message": False,
        "is_active": True
    }
]
```

### 5.2 启动时连接
在 `main.py` 的 lifespan 中：
```python
# 启动所有已激活的机器人
async with AsyncSessionLocal() as bot_session:
    result = await bot_session.execute(
        select(Bot).where(Bot.is_active == True)
    )
    active_bots = result.scalars().all()
    for bot in active_bots:
        await channel_service.start_bot(bot.bot_id)
```

## 六、API 接口

### 6.1 Bot 管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/bots | 获取所有机器人 |
| POST | /api/v1/bots | 创建机器人 |
| GET | /api/v1/bots/{bot_id} | 获取机器人详情 |
| PUT | /api/v1/bots/{bot_id} | 更新机器人 |
| DELETE | /api/v1/bots/{bot_id} | 删除机器人 |

### 6.2 Bot 控制
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/bots/{bot_id}/start | 启动机器人 |
| POST | /api/v1/bots/{bot_id}/stop | 停止机器人 |

### 6.3 OneBot 配置
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/bots/{bot_id}/config | 获取 OneBot 配置 |
| PUT | /api/v1/bots/{bot_id}/config | 更新 OneBot 配置 |

## 七、消息格式

### 7.1 ChannelMessage 统一格式
```python
ChannelMessage(
    session_id: str,      # 会话 ID (onebot11_private_xxx 或 onebot11_group_xxx)
    channel_type: str,    # 渠道类型
    user_id: str,         # 用户 ID
    content: str,          # 消息内容
    role: str,             # 角色 (user/assistant)
    message_id: str,       # 消息 ID
    channel_id: str,       # 频道 ID
    group_id: Optional[str], # 群 ID (群聊时)
    metadata: Dict          # 额外元数据
)
```

### 7.2 会话 ID 生成规则
- 私聊: `onebot11_private_{user_id}`
- 群聊: `onebot11_group_{group_id}_{user_id}`

## 八、配置说明

### 8.1 NapCat 端配置
在 NapCat 的 `config.json` 或 `napcat.json` 中：
```json
{
  "websocket": {
    "enabled": true,
    "url": "ws://127.0.0.1:6199/ws"
  }
}
```

### 8.2 注意事项
- NapCat 版本需要支持反向 WebSocket
- URL 地址 `ws://127.0.0.1:6199/ws` 中的 `/ws` 后缀是必须的
- 如果 NapCat 和 HAXAtom 不在同一台机器，将 `127.0.0.1` 改为实际 IP

## 九、目录结构

```
backend/app/
├── channels/
│   ├── __init__.py
│   ├── service.py              # 渠道服务
│   └── adapters/
│       ├── __init__.py
│       ├── base.py            # 适配器基类
│       └── onebot11.py        # OneBot v11 适配器
├── models/
│   ├── bot.py                 # Bot 模型
│   └── onebot11_config.py     # OneBot 配置模型
├── schemas/
│   └── bot.py                 # Pydantic schemas
├── api/v1/endpoints/
│   └── bots.py                # Bot API 路由
└── db/
    └── init_data.py           # 初始化默认数据
```

## 十、已知问题与解决方案

### 10.1 aiocqhttp API 兼容性
**问题:** `event.dict()` 方法不存在
**解决:** 直接使用 `event` 对象，它本身已经包含所有数据

### 10.2 任务被垃圾回收
**问题:** `asyncio.create_task()` 创建的任务被 GC
**解决:** 保存任务引用到 `self._server_task`

## 十一、后续扩展

### 11.1 新增渠道
1. 在 `app/models/` 创建渠道配置模型
2. 在 `app/channels/adapters/` 创建适配器
3. 在 `app/db/init_data.py` 添加默认配置
4. 在 `ChannelService` 注册适配器

### 11.2 支持的渠道
- [x] OneBot v11 (QQ / NapCat)
- [ ] 飞书
- [ ] Discord
- [ ] Telegram
