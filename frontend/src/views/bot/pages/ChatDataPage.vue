<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  listConversations,
  getConversation,
  deleteConversation,
  clearConversation,
  type Conversation,
  type Message,
} from "../../../api/chat";
import { getPresets, type PresetListItem } from "../../../api/preset";
import { t } from "../../../locales";

const $t = computed(() => t);

// 状态
const conversations = ref<Conversation[]>([]);
const selectedConversation = ref<Conversation | null>(null);
const presetList = ref<PresetListItem[]>([]);
const loading = ref(false);
const detailLoading = ref(false);

// 过滤条件
const filters = ref({
  preset_id: "",
  channel_type: "",
  search: "",
});

const channelTypes = [
  { value: "web", label: "Web" },
  { value: "qq", label: "QQ" },
  { value: "qq_group", label: "QQ群" },
  { value: "qq_private", label: "QQ私聊" },
  { value: "feishu", label: "飞书" },
  { value: "dingtalk", label: "钉钉" },
  { value: "telegram", label: "Telegram" },
];

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
});

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return "-";
  const date = new Date(time);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// 格式化相对时间
const formatRelativeTime = (time: string) => {
  if (!time) return "-";
  const now = Date.now();
  const date = new Date(time).getTime();
  const diff = now - date;

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;
  return formatTime(time);
};

// 获取会话列表
const fetchConversations = async () => {
  loading.value = true;
  try {
    const params: any = {
      skip: (pagination.value.page - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize,
    };
    if (filters.value.preset_id) params.preset_id = filters.value.preset_id;
    if (filters.value.channel_type)
      params.channel_type = filters.value.channel_type;

    const res = await listConversations(params);
    if ((res.code === 0 || res.code === 200) && res.data) {
      conversations.value = res.data;
      pagination.value.total = res.data.length || 0;
    }
  } catch (error: any) {
    ElMessage.error(error.message || "获取会话列表失败");
  } finally {
    loading.value = false;
  }
};

// 获取预设列表
const fetchPresets = async () => {
  try {
    const res = await getPresets();
    if ((res.code === 0 || res.code === 200) && res.data) {
      presetList.value = res.data;
    }
  } catch (error: any) {
    console.error("获取预设列表失败:", error);
  }
};

// 获取会话详情
const fetchConversationDetail = async (sessionId: string) => {
  detailLoading.value = true;
  try {
    const res = await getConversation(sessionId);
    if ((res.code === 0 || res.code === 200) && res.data) {
      selectedConversation.value = res.data;
    }
  } catch (error: any) {
    ElMessage.error(error.message || "获取会话详情失败");
  } finally {
    detailLoading.value = false;
  }
};

// 选择会话
const selectConversation = async (conv: Conversation) => {
  await fetchConversationDetail(conv.session_id);
};

// 关闭详情
const closeDetail = () => {
  selectedConversation.value = null;
};

// 删除会话
const handleDelete = async (conv: Conversation) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除会话"${conv.title}"吗？此操作不可恢复。`,
      "删除确认",
      {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    const res = await deleteConversation(conv.session_id);
    if (res.code === 0) {
      ElMessage.success("删除成功");
      fetchConversations();
      if (selectedConversation.value?.session_id === conv.session_id) {
        closeDetail();
      }
    } else {
      ElMessage.error(res.message || "删除失败");
    }
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error(error.message || "删除失败");
    }
  }
};

// 清空会话消息
const handleClear = async (conv: Conversation) => {
  try {
    await ElMessageBox.confirm(
      `确定要清空会话"${conv.title}"的所有消息吗？`,
      "清空确认",
      {
        confirmButtonText: "清空",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    const res = await clearConversation(conv.session_id);
    if (res.code === 0) {
      ElMessage.success("清空成功");
      fetchConversations();
      if (selectedConversation.value?.session_id === conv.session_id) {
        selectedConversation.value = res.data;
      }
    } else {
      ElMessage.error(res.message || "清空失败");
    }
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error(error.message || "清空失败");
    }
  }
};

// 过滤变化
const handleFilterChange = () => {
  pagination.value.page = 1;
  fetchConversations();
};

// 分页变化
const handlePageChange = (page: number) => {
  pagination.value.page = page;
  fetchConversations();
};

// 获取消息角色标签
const getRoleLabel = (role: string) => {
  const map: Record<string, string> = {
    system: "系统",
    user: "用户",
    assistant: "AI",
    tool: "工具",
  };
  return map[role] || role;
};

// 获取消息角色颜色
const getRoleClass = (role: string) => {
  const map: Record<string, string> = {
    system: "role-system",
    user: "role-user",
    assistant: "role-assistant",
    tool: "role-tool",
  };
  return map[role] || "";
};

// 获取平台标签
const getChannelLabel = (type: string) => {
  const item = channelTypes.find((t) => t.value === type);
  return item ? item.label : type;
};

// 搜索防抖
let searchTimer: any = null;
const handleSearch = () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    handleFilterChange();
  }, 300);
};

// 初始化
onMounted(() => {
  fetchConversations();
  fetchPresets();
});
</script>

<template>
  <div class="chat-data-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        对话数据
      </h1>
      <p class="page-description">
        管理和查看所有对话记录，支持按平台类型和预设方案筛选
      </p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-value">{{ conversations.length }}</div>
        <div class="stat-label">当前页面</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ pagination.total }}</div>
        <div class="stat-label">会话总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ presetList.length }}</div>
        <div class="stat-label">预设方案</div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧会话列表 -->
      <div class="conversation-list-panel">
        <!-- 工具栏 -->
        <div class="toolbar">
          <div class="toolbar-left">
            <button
              class="btn btn-primary"
              @click="fetchConversations"
              :disabled="loading"
            >
              <svg
                class="icon"
                :class="{ spinning: loading }"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              刷新
            </button>
          </div>
          <div class="toolbar-right">
            <input
              v-model="filters.search"
              class="search-input"
              type="text"
              placeholder="搜索会话标题..."
              @input="handleSearch"
            />
          </div>
        </div>

        <!-- 过滤器 -->
        <div class="filters">
          <select
            v-model="filters.channel_type"
            class="filter-select"
            @change="handleFilterChange"
          >
            <option value="">全部平台</option>
            <option
              v-for="type in channelTypes"
              :key="type.value"
              :value="type.value"
            >
              {{ type.label }}
            </option>
          </select>
          <select
            v-model="filters.preset_id"
            class="filter-select"
            @change="handleFilterChange"
          >
            <option value="">全部预设</option>
            <option
              v-for="preset in presetList"
              :key="preset.preset_id"
              :value="preset.preset_id"
            >
              {{ preset.preset_name }}
            </option>
          </select>
        </div>

        <!-- 会话列表 -->
        <div class="conversation-list">
          <div v-if="loading" class="loading-placeholder">
            <svg
              class="spinning"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            加载中...
          </div>
          <div v-else-if="conversations.length === 0" class="empty-placeholder">
            暂无会话数据
          </div>
          <div
            v-else
            v-for="conv in conversations"
            :key="conv.session_id"
            class="conversation-item"
            :class="{
              active: selectedConversation?.session_id === conv.session_id,
            }"
            @click="selectConversation(conv)"
          >
            <div class="conversation-info">
              <div class="conversation-header">
                <span class="conversation-title">{{ conv.title }}</span>
                <span class="channel-badge">{{
                  getChannelLabel(conv.channel_type)
                }}</span>
              </div>
              <div class="conversation-meta">
                <span class="preset-name">{{ conv.preset_id }}</span>
                <span class="message-count"
                  >{{ conv.message_count }} 条消息</span
                >
              </div>
              <div class="conversation-time">
                {{ formatRelativeTime(conv.updated_at) }}
              </div>
            </div>
            <div class="conversation-actions">
              <button
                class="icon-btn"
                @click.stop="handleClear(conv)"
                title="清空"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
              <button
                class="icon-btn danger"
                @click.stop="handleDelete(conv)"
                title="删除"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination" v-if="pagination.total > 0">
          <button
            class="page-btn"
            :disabled="pagination.page === 1"
            @click="handlePageChange(pagination.page - 1)"
          >
            上一页
          </button>
          <span class="page-info"
            >{{ pagination.page }} /
            {{ Math.ceil(pagination.total / pagination.pageSize) || 1 }}</span
          >
          <button
            class="page-btn"
            :disabled="
              pagination.page >=
              Math.ceil(pagination.total / pagination.pageSize)
            "
            @click="handlePageChange(pagination.page + 1)"
          >
            下一页
          </button>
        </div>
      </div>

      <!-- 右侧会话详情 -->
      <div class="conversation-detail-panel" v-if="selectedConversation">
        <div class="detail-header">
          <div class="detail-title">
            <h2>{{ selectedConversation.title }}</h2>
            <span class="channel-badge">{{
              getChannelLabel(selectedConversation.channel_type)
            }}</span>
          </div>
          <button class="close-btn" @click="closeDetail">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div class="detail-meta">
          <div class="meta-item">
            <span class="meta-label">会话ID:</span>
            <span class="meta-value">{{
              selectedConversation.session_id
            }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">预设方案:</span>
            <span class="meta-value">{{ selectedConversation.preset_id }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">消息数:</span>
            <span class="meta-value">{{
              selectedConversation.message_count
            }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">创建时间:</span>
            <span class="meta-value">{{
              formatTime(selectedConversation.created_at)
            }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">更新时间:</span>
            <span class="meta-value">{{
              formatTime(selectedConversation.updated_at)
            }}</span>
          </div>
        </div>

        <div class="detail-loading" v-if="detailLoading">
          <svg
            class="spinning"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          加载消息中...
        </div>

        <div v-else class="message-list">
          <div
            v-if="
              !selectedConversation.messages ||
              selectedConversation.messages.length === 0
            "
            class="empty-messages"
          >
            暂无消息
          </div>
          <div
            v-for="(msg, index) in selectedConversation.messages"
            :key="index"
            class="message-item"
            :class="getRoleClass(msg.role)"
          >
            <div class="message-header">
              <span class="message-role">{{ getRoleLabel(msg.role) }}</span>
              <span class="message-time" v-if="msg.timestamp">{{
                formatTime(msg.timestamp)
              }}</span>
            </div>
            <div class="message-content">
              <pre>{{ msg.content }}</pre>
            </div>
            <div
              v-if="msg.tool_calls && msg.tool_calls.length > 0"
              class="message-tool-calls"
            >
              <div
                class="tool-call"
                v-for="(call, i) in msg.tool_calls"
                :key="i"
              >
                <span class="tool-name">{{
                  call.name || call.function?.name
                }}</span>
                <pre class="tool-args">{{
                  typeof call.arguments === "string"
                    ? call.arguments
                    : JSON.stringify(
                        call.arguments || call.function?.arguments,
                        null,
                        2,
                      )
                }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="detail-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <p>选择左侧会话查看详情</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-data-page {
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.page-title .icon {
  width: 28px;
  height: 28px;
  color: var(--color-primary);
}

.page-description {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}

.stats-section {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-card);
  border-radius: 8px;
  padding: 16px 24px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.main-content {
  display: flex;
  gap: 24px;
  flex: 1;
  min-height: 0;
}

.conversation-list-panel {
  width: 400px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.search-input {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  width: 160px;
  background: var(--bg-input);
  color: var(--text-primary);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.filters {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.filter-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  background: var(--bg-input);
  color: var(--text-primary);
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-primary);
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.loading-placeholder,
.empty-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: var(--text-secondary);
}

.conversation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.conversation-item:hover {
  background: var(--bg-hover);
}

.conversation-item.active {
  background: var(--color-primary-light);
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.conversation-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.channel-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--bg-hover);
  color: var(--text-secondary);
  white-space: nowrap;
}

.conversation-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.conversation-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.conversation-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .conversation-actions {
  opacity: 1;
}

.icon-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.icon-btn.danger:hover {
  background: #fee;
  color: #d32f2f;
}

.icon-btn svg {
  width: 16px;
  height: 16px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
}

.page-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: var(--bg-hover);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: var(--text-secondary);
}

.conversation-detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  min-width: 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-title h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.meta-item {
  display: flex;
  gap: 6px;
  font-size: 13px;
}

.meta-label {
  color: var(--text-secondary);
}

.meta-value {
  color: var(--text-primary);
  font-weight: 500;
}

.detail-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: var(--text-secondary);
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.empty-messages {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--text-secondary);
}

.message-item {
  margin-bottom: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  background: var(--bg-secondary);
}

.message-item.role-user {
  background: #e3f2fd;
}

.message-item.role-assistant {
  background: #f3e5f5;
}

.message-item.role-tool {
  background: #fff3e0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-role {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--color-primary);
  color: white;
}

.role-user .message-role {
  background: #1976d2;
}

.role-assistant .message-role {
  background: #7b1fa2;
}

.role-tool .message-role {
  background: #e65100;
}

.message-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.message-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
}

.message-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}

.message-tool-calls {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border-color);
}

.tool-call {
  margin-top: 8px;
}

.tool-name {
  font-size: 12px;
  font-weight: 600;
  color: #e65100;
}

.tool-args {
  margin: 4px 0 0 0;
  padding: 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.detail-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: var(--bg-card);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  color: var(--text-secondary);
}

.detail-empty svg {
  width: 64px;
  height: 64px;
  opacity: 0.5;
}

.icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
