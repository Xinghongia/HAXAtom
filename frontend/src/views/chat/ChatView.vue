<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { t } from "../../locales";
import {
  sendChatMessage,
  sendChatMessageStream,
  listPresets,
  listConversations,
  getConversation,
} from "../../api/chat";
import MarkdownRenderer from "../../components/MarkdownRenderer.vue";

const route = useRoute();
const router = useRouter();

// ChatView 使用自己独立的侧边栏状态，不使用全局的
const localSidebarCollapsed = ref(false);

const messageInput = ref("");
const messages = ref([]);
const isLoading = ref(false);
const currentSessionId = ref("");
const currentPreset = ref(null);
const presets = ref([]);
const conversations = ref([]); // 对话历史列表
const showAddMenu = ref(false);
const showConfigDialog = ref(false);
const selectedPresetId = ref("");
const selectedConfigName = ref("未选择");
const streamEnabled = ref(true);
const showMarkdownPreview = ref(false);

// 操作菜单相关
const activeActionMenu = ref<string | null>(null);
const actionMenuPosition = ref({});

// 切换操作菜单
const toggleChatActionMenu = (sessionId: string, event: MouseEvent) => {
  if (activeActionMenu.value === sessionId) {
    activeActionMenu.value = null;
  } else {
    activeActionMenu.value = sessionId;
    // 计算菜单位置 - 显示在按钮右侧
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    actionMenuPosition.value = {
      top: `${rect.top}px`,
      left: `${rect.right + 8}px`,
    };
  }
};

// 删除会话
const deleteConversation = async (sessionId: string) => {
  if (!confirm("确定要删除这个会话吗？")) return;

  try {
    const response = await import("../../api/chat");
    const result = await response.deleteConversation(sessionId);
    if (result.code === 200) {
      // 从列表中移除
      conversations.value = conversations.value.filter(
        (c) => c.session_id !== sessionId,
      );
      // 如果删除的是当前会话，清空消息
      if (sessionId === currentSessionId.value) {
        currentSessionId.value = "";
        messages.value = [];
      }
      activeActionMenu.value = null;
    }
  } catch (error) {
    console.error("删除会话失败:", error);
  }
};

// 置顶会话
const pinConversation = (sessionId: string) => {
  console.log("置顶会话:", sessionId);
  activeActionMenu.value = null;
  // TODO: 实现置顶功能
};

// 分享会话
const shareConversation = (sessionId: string) => {
  console.log("分享会话:", sessionId);
  activeActionMenu.value = null;
  // TODO: 实现分享功能
};

// 重命名会话
const renameConversation = (sessionId: string) => {
  const newTitle = prompt("请输入新的会话标题:");
  if (newTitle) {
    console.log("重命名会话:", sessionId, newTitle);
    // TODO: 实现重命名功能
  }
  activeActionMenu.value = null;
};

// 举报会话
const reportConversation = (sessionId: string) => {
  console.log("举报会话:", sessionId);
  activeActionMenu.value = null;
  // TODO: 实现举报功能
};

// 复制消息内容
const copyMessageContent = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content);
    // 显示提示
    showCopyToast();
  } catch (err) {
    console.error("复制失败:", err);
  }
};

// 复制成功提示
const showCopyToast = () => {
  const isDark = document.documentElement.classList.contains("dark");
  const toast = document.createElement("div");
  toast.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px;">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
    <span>已复制</span>
  `;
  toast.style.cssText = `
    position: fixed;
    top: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: ${isDark ? "rgba(45, 45, 45, 0.95)" : "rgba(255, 255, 255, 0.95)"};
    color: ${isDark ? "#e0e0e0" : "#333"};
    padding: 10px 18px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    z-index: 9999;
    display: flex;
    align-items: center;
    box-shadow: ${isDark ? "0 4px 12px rgba(0, 0, 0, 0.4)" : "0 4px 12px rgba(0, 0, 0, 0.15)"};
    border: 1px solid ${isDark ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.08)"};
    backdrop-filter: blur(8px);
    animation: toastSlideIn 0.3s ease;
  `;
  document.body.appendChild(toast);

  // 添加动画样式
  const style = document.createElement("style");
  style.textContent = `
    @keyframes toastSlideIn {
      0% { opacity: 0; transform: translateX(-50%) translateY(-16px) scale(0.95); }
      100% { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
    }
    @keyframes toastSlideOut {
      0% { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
      100% { opacity: 0; transform: translateX(-50%) translateY(-16px) scale(0.95); }
    }
  `;
  document.head.appendChild(style);

  // 2秒后消失
  setTimeout(() => {
    toast.style.animation = "toastSlideOut 0.2s ease forwards";
    setTimeout(() => {
      toast.remove();
      style.remove();
    }, 200);
  }, 1800);
};

// 打字机效果
const displayText = ref("");
const fullText = "Hello! HAXAtom";
let charIndex = 0;
let typingTimer: number | null = null;

// 聊天内容容器 ref（可滚动区域）
const chatContentRef = ref<HTMLElement | null>(null);

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContentRef.value) {
      chatContentRef.value.scrollTop = chatContentRef.value.scrollHeight;
    }
  });
};

// Markdown 预览切换
const toggleMarkdownPreview = () => {
  showMarkdownPreview.value = !showMarkdownPreview.value;
};

const startTypewriter = () => {
  charIndex = 0;
  displayText.value = "";
  if (typingTimer) clearInterval(typingTimer);

  typingTimer = window.setInterval(() => {
    if (charIndex < fullText.length) {
      displayText.value += fullText[charIndex];
      charIndex++;
    } else {
      if (typingTimer) {
        clearInterval(typingTimer);
        typingTimer = null;
      }
    }
  }, 100); // 每个字间隔 100ms
};

// 切换侧边栏
const toggleSidebar = () => {
  localSidebarCollapsed.value = !localSidebarCollapsed.value;
};

// 翻译函数
const $t = computed(() => t);

// 格式化打字机文本，将 HAXAtom 用特殊样式包裹
const formattedText = computed(() => {
  const parts = displayText.value.split("HAXAtom");
  if (parts.length === 2) {
    return `${parts[0]}<span class="highlight">HAXAtom</span>${parts[1]}`;
  }
  return displayText.value;
});

// 加载预设列表
const loadPresets = async () => {
  try {
    const response = await listPresets();
    if (response.code === 200) {
      presets.value = response.data;
      // 设置默认预设
      const defaultPreset =
        response.data.find((p) => p.is_default) || response.data[0];
      if (defaultPreset) {
        currentPreset.value = defaultPreset;
        selectedPresetId.value = defaultPreset.preset_id;
        selectedConfigName.value = defaultPreset.preset_name;
      }
    }
  } catch (error) {
    console.error("加载预设失败:", error);
  }
};

// 加载对话历史
const loadConversations = async () => {
  try {
    const response = await listConversations();
    if (response.code === 200) {
      conversations.value = response.data;
    }
  } catch (error) {
    console.error("加载对话历史失败:", error);
  }
};

// 切换对话
const switchConversation = (sessionId: string, event?: MouseEvent) => {
  // 如果点击的是操作按钮或菜单，不切换会话
  if (event) {
    const target = event.target as HTMLElement;
    if (
      target.closest(".chat-item-actions") ||
      target.closest(".chat-action-menu")
    ) {
      return;
    }
  }
  // 关闭操作菜单
  activeActionMenu.value = null;
  // 使用路由跳转
  router.push(`/chat/${sessionId}`);
};

// 格式化时间显示
const formatMessageTime = (timestamp: any): string => {
  if (!timestamp) return "";

  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return "";

  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();

  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  const isYesterday = date.toDateString() === yesterday.toDateString();

  const timeStr = date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  if (isToday) {
    return `今天 ${timeStr}`;
  } else if (isYesterday) {
    return `昨天 ${timeStr}`;
  } else {
    const dateStr = date.toLocaleDateString([], {
      month: "short",
      day: "numeric",
    });
    return `${dateStr} ${timeStr}`;
  }
};

// 从路由加载会话
const loadSessionFromRoute = () => {
  const sessionId = route.params.sessionId as string;
  if (sessionId) {
    currentSessionId.value = sessionId;
    // 加载该会话的历史消息
    loadConversationMessages(sessionId);
  }
};

// 加载会话消息
const loadConversationMessages = async (sessionId: string) => {
  try {
    const response = await getConversation(sessionId);
    if (response.code === 200) {
      // 转换消息格式
      messages.value = (response.data.messages || []).map((msg: any) => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp ? new Date(msg.timestamp) : null,
      }));
      // 加载完成后滚动到底部
      scrollToBottom();
    }
  } catch (error) {
    console.error("加载会话消息失败:", error);
  }
};

// 切换配置菜单
const toggleConfigMenu = () => {
  showConfigMenu.value = !showConfigMenu.value;
};

// 切换添加菜单
const toggleAddMenu = () => {
  showAddMenu.value = !showAddMenu.value;
};

// 打开文件上传
const openFileUpload = () => {
  // TODO: 实现文件上传功能
  console.log("打开文件上传");
  // 不关闭菜单
};

// 打开配置文件弹窗
const openConfigDialog = () => {
  showConfigDialog.value = true;
  // 不关闭添加菜单
};

// 关闭配置文件弹窗
const closeConfigDialog = () => {
  showConfigDialog.value = false;
};

// 选择预设
const selectPreset = (preset) => {
  selectedPresetId.value = preset.preset_id;
  selectedConfigName.value = preset.preset_name;
  // 不关闭弹窗，等待用户点击应用按钮
};

// 确认配置
const confirmConfig = () => {
  if (selectedPresetId.value) {
    const preset = presets.value.find(
      (p) => p.preset_id === selectedPresetId.value,
    );
    if (preset) {
      currentPreset.value = preset;
      // 切换预设时创建新会话
      currentSessionId.value = "";
      messages.value = [];
    }
  }
  closeConfigDialog();
  // 不关闭添加菜单
};

// 切换流式响应
const toggleStream = () => {
  streamEnabled.value = !streamEnabled.value;
  // 不关闭菜单，保持打开状态
};

// 发送消息
const sendMessage = async () => {
  if (!messageInput.value.trim() || isLoading.value) return;
  if (!currentPreset.value) {
    alert("请先选择预设方案");
    return;
  }

  const userMessage = messageInput.value.trim();
  messageInput.value = "";

  // 添加用户消息到列表
  messages.value.push({
    role: "user",
    content: userMessage,
    timestamp: new Date(),
  });

  // 发送消息后滚动到底部
  scrollToBottom();

  isLoading.value = true;

  // 添加AI占位消息
  const aiMessageIndex = messages.value.length;
  messages.value.push({
    role: "assistant",
    content: "",
    timestamp: new Date(),
  });

  // 添加AI消息后滚动到底部
  scrollToBottom();

  try {
    if (streamEnabled.value) {
      // 流式响应
      await sendChatMessageStream(
        {
          preset_id: currentPreset.value.preset_id,
          message: userMessage,
          session_id: currentSessionId.value || undefined,
          stream: true,
          enable_memory: true,
          enable_tools: true,
          enable_rag: true,
          channel_type: "web",
        },
        // onChunk - 收到流式数据
        (chunk) => {
          // 收到第一个 chunk 时关闭 loading 状态
          if (isLoading.value) {
            isLoading.value = false;
          }
          // 使用展开运算符触发响应式更新
          const updatedMessages = [...messages.value];
          updatedMessages[aiMessageIndex] = {
            ...updatedMessages[aiMessageIndex],
            content: updatedMessages[aiMessageIndex].content + chunk,
          };
          messages.value = updatedMessages;
          // 流式输出时滚动到底部
          scrollToBottom();
        },
        // onComplete - 完成
        async (fullResponse, sessionId) => {
          currentSessionId.value = sessionId;
          isLoading.value = false;
          // 刷新对话历史并跳转到新会话
          await loadConversations();
          await router.push(`/chat/${sessionId}`);
        },
        // onError - 错误
        (error) => {
          console.error("流式响应错误:", error);
          messages.value[aiMessageIndex].content =
            "[错误] " + (error.message || "请求失败");
          isLoading.value = false;
        },
      );
    } else {
      // 非流式响应
      const response = await sendChatMessage({
        preset_id: currentPreset.value.preset_id,
        message: userMessage,
        session_id: currentSessionId.value || undefined,
        stream: false,
        enable_memory: true,
        enable_tools: true,
        enable_rag: true,
        channel_type: "web",
      });

      if (response.code === 200) {
        messages.value[aiMessageIndex].content = response.data.content;
        currentSessionId.value = response.data.session_id;
        // 刷新对话历史并跳转到新会话
        await loadConversations();
        router.push(`/chat/${response.data.session_id}`);
      } else {
        messages.value[aiMessageIndex].content =
          "[错误] " + (response.message || "请求失败");
      }
      isLoading.value = false;
    }
  } catch (error) {
    console.error("发送消息失败:", error);
    messages.value[aiMessageIndex].content =
      "[错误] " + (error.message || "网络错误");
    isLoading.value = false;
  }
};

// 处理键盘事件
const handleKeyPress = (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
};

// 点击外部关闭菜单
const handleClickOutside = (event) => {
  // 关闭配置菜单
  const menu = document.querySelector(".config-menu");
  const button = document.querySelector(".action-btn");
  if (
    menu &&
    button &&
    !menu.contains(event.target) &&
    !button.contains(event.target)
  ) {
    showConfigMenu.value = false;
  }

  // 关闭添加菜单
  const addMenu = document.querySelector(".add-menu, .add-menu-bottom");
  const addBtn = document.querySelector(".add-btn-center, .add-btn");
  if (
    addMenu &&
    addBtn &&
    !addMenu.contains(event.target) &&
    !addBtn.contains(event.target)
  ) {
    showAddMenu.value = false;
  }

  // 关闭操作菜单
  const actionMenu = document.querySelector(".chat-action-menu");
  const actionBtn = document.querySelector(".chat-more-btn");
  if (
    actionMenu &&
    actionBtn &&
    !actionMenu.contains(event.target) &&
    !actionBtn.contains(event.target)
  ) {
    activeActionMenu.value = null;
  }
};

// 初始化
onMounted(() => {
  loadPresets();
  loadConversations();
  startTypewriter();
  document.addEventListener("click", handleClickOutside);
  // 从路由加载会话
  loadSessionFromRoute();
});

// 监听路由变化
watch(
  () => route.params.sessionId,
  (newSessionId, oldSessionId) => {
    // 只有当路由真正变化且不是当前正在聊天的会话时才加载
    if (
      newSessionId &&
      newSessionId !== oldSessionId &&
      newSessionId !== currentSessionId.value
    ) {
      loadSessionFromRoute();
    }
  },
);
</script>

<template>
  <div class="chat-container">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: localSidebarCollapsed }">
      <div class="sidebar-header">
        <button
          class="collapse-btn"
          @click="toggleSidebar"
          title="收起/展开侧边栏"
        >
          <svg
            class="icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M3 12h18M3 6h18M3 18h18" v-if="localSidebarCollapsed" />
            <path d="M3 6h18M3 12h18M3 18h18" v-else />
          </svg>
        </button>
      </div>

      <div class="sidebar-content">
        <div
          class="new-chat-btn"
          :class="{ active: !currentSessionId }"
          @click="
            messages = [];
            currentSessionId = '';
            router.push('/chat');
          "
        >
          <svg
            class="icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M12 5v14M5 12h14" />
          </svg>
          <span>{{ $t("chat.newChat") }}</span>
        </div>

        <div class="chat-history">
          <div class="chat-history-title">{{ $t("chat.history") }}</div>
          <div class="chat-list">
            <div
              v-for="conv in conversations"
              :key="conv.session_id"
              class="chat-item"
              :class="{ active: currentSessionId === conv.session_id }"
              @click="switchConversation(conv.session_id, $event)"
            >
              <div class="chat-item-content">
                <svg
                  class="chat-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
                  />
                </svg>
                <span class="chat-title">{{ conv.title || "未命名会话" }}</span>
              </div>
              <div class="chat-item-actions" @click.stop>
                <button
                  class="chat-more-btn"
                  @click="toggleChatActionMenu(conv.session_id, $event)"
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <circle cx="12" cy="12" r="1" />
                    <circle cx="19" cy="12" r="1" />
                    <circle cx="5" cy="12" r="1" />
                  </svg>
                </button>
                <!-- 操作菜单 -->
                <div
                  v-if="activeActionMenu === conv.session_id"
                  class="chat-action-menu"
                  :style="actionMenuPosition"
                  @click.stop
                >
                  <div
                    class="menu-item"
                    @click.stop="pinConversation(conv.session_id)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path d="M12 19V5M5 12l7-7 7 7" />
                    </svg>
                    <span>置顶</span>
                  </div>
                  <div
                    class="menu-item"
                    @click.stop="shareConversation(conv.session_id)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                      <polyline points="16 6 12 2 8 6" />
                      <line x1="12" y1="2" x2="12" y2="15" />
                    </svg>
                    <span>分享</span>
                  </div>
                  <div
                    class="menu-item"
                    @click.stop="renameConversation(conv.session_id)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path
                        d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                      />
                      <path
                        d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
                      />
                    </svg>
                    <span>重命名</span>
                  </div>
                  <div
                    class="menu-item"
                    @click.stop="reportConversation(conv.session_id)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path
                        d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
                      />
                      <line x1="12" y1="9" x2="12" y2="13" />
                      <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                    <span>举报</span>
                  </div>
                  <div
                    class="menu-item danger"
                    @click.stop="deleteConversation(conv.session_id)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <polyline points="3 6 5 6 21 6" />
                      <path
                        d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                      />
                    </svg>
                    <span>删除</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="conversations.length === 0" class="no-history">
              暂无历史对话
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <main class="chat-main">
      <div ref="chatContentRef" class="chat-content">
        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="empty-state">
          <div class="welcome-text">
            <h1>
              <span class="typewriter">
                <span v-html="formattedText"></span>
              </span>
              <svg class="welcome-icon" viewBox="0 0 24 24" fill="#FFD700">
                <path
                  d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                />
              </svg>
            </h1>
          </div>
          <!-- 空状态时的输入框（居中显示） -->
          <div class="input-wrapper-center">
            <div class="modern-input-container-center">
              <!-- 上层：文本输入区域 -->
              <textarea
                v-model="messageInput"
                :placeholder="
                  currentPreset ? 'Ask HAXAtom...' : '请先选择预设方案'
                "
                @keydown="handleKeyPress"
                rows="1"
                class="modern-chat-input-center"
                :disabled="!currentPreset || isLoading"
              ></textarea>

              <!-- Markdown 预览区域 -->
              <div
                v-if="showMarkdownPreview && messageInput"
                class="markdown-preview-container"
              >
                <MarkdownRenderer :content="messageInput" />
              </div>

              <!-- 下层：按钮区域 -->
              <div class="input-actions-center">
                <div class="input-left">
                  <div class="add-btn-wrapper">
                    <button
                      class="add-btn-center"
                      @click="toggleAddMenu"
                      title="添加"
                    >
                      <svg
                        class="icon"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <path d="M12 5v14M5 12h14" />
                      </svg>
                    </button>

                    <!-- 一级菜单 -->
                    <div v-if="showAddMenu" class="add-menu">
                      <div class="menu-item" @click="openFileUpload">
                        <svg
                          class="menu-icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        >
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                          <polyline points="17 8 12 3 7 8" />
                          <line x1="12" y1="3" x2="12" y2="15" />
                        </svg>
                        <span>上传文件</span>
                      </div>
                      <div class="menu-item" @click="openConfigDialog">
                        <svg
                          class="menu-icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        >
                          <circle cx="12" cy="12" r="3" />
                          <path
                            d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
                          />
                        </svg>
                        <div class="menu-item-content">
                          <span>配置文件</span>
                          <span class="menu-subtitle">{{
                            selectedConfigName
                          }}</span>
                        </div>
                        <svg
                          class="menu-arrow"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        >
                          <polyline points="9 18 15 12 9 6" />
                        </svg>
                      </div>
                      <div
                        class="menu-item stream-toggle"
                        @click="toggleStream"
                      >
                        <svg
                          class="menu-icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        >
                          <polygon
                            points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"
                          />
                        </svg>
                        <span>{{
                          streamEnabled ? "流式响应已开启" : "流式响应已关闭"
                        }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="input-right">
                  <button
                    class="voice-btn-center"
                    title="语音输入"
                    :disabled="isLoading"
                  >
                    <svg
                      class="icon"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path
                        d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"
                      />
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                      <line x1="12" y1="19" x2="12" y2="23" />
                      <line x1="8" y1="23" x2="16" y2="23" />
                    </svg>
                  </button>
                  <button
                    class="send-btn-center"
                    @click="sendMessage"
                    :disabled="
                      !messageInput.trim() || isLoading || !currentPreset
                    "
                    title="发送"
                  >
                    <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 配置文件选择弹窗 -->
        <div
          v-if="showConfigDialog"
          class="modal-overlay"
          @click="closeConfigDialog"
        >
          <div class="config-modal" @click.stop>
            <div class="modal-header">
              <h2>选择配置文件</h2>
              <button class="modal-close" @click="closeConfigDialog">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div class="modal-content">
              <div class="config-list">
                <div
                  v-for="preset in presets"
                  :key="preset.preset_id"
                  class="config-item"
                  :class="{ active: selectedPresetId === preset.preset_id }"
                  @click="selectPreset(preset)"
                >
                  <div class="config-item-header">
                    <span class="config-item-name">{{
                      preset.preset_name
                    }}</span>
                    <svg
                      v-if="selectedPresetId === preset.preset_id"
                      class="check-icon"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                  <span class="config-item-id">{{ preset.preset_id }}</span>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn-cancel" @click="closeConfigDialog">
                取消
              </button>
              <button class="btn-confirm" @click="confirmConfig">应用</button>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="message-list">
          <div
            v-for="(message, index) in messages"
            :key="index"
            class="message-wrapper"
            :class="message.role"
          >
            <!-- 用户消息 -->
            <div v-if="message.role === 'user'" class="user-message">
              <div class="message-bubble-user">{{ message.content }}</div>
            </div>

            <!-- AI 消息 -->
            <div
              v-else-if="!(isLoading && index === messages.length - 1)"
              class="assistant-message"
            >
              <div class="assistant-avatar">
                <img src="/15.jpg" alt="AI" class="ai-avatar-img" />
              </div>
              <div class="assistant-content">
                <div class="message-text-assistant markdown-body">
                  <MarkdownRenderer :content="message.content" />
                </div>
                <div class="message-meta">
                  <span class="message-time">
                    {{ formatMessageTime(message.timestamp) }}
                  </span>
                  <div class="message-actions">
                    <button
                      class="action-btn"
                      title="复制"
                      @click="copyMessageContent(message.content)"
                    >
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <rect
                          x="9"
                          y="9"
                          width="13"
                          height="13"
                          rx="2"
                          ry="2"
                        />
                        <path
                          d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                        />
                      </svg>
                    </button>
                    <button class="action-btn" title="回复">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <polyline points="9 14 4 9 9 4" />
                        <path d="M20 20v-7a4 4 0 0 0-4-4H4" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载中状态 -->
          <div v-if="isLoading" class="message-wrapper assistant loading">
            <div class="assistant-avatar">
              <img src="/15.jpg" alt="AI" class="ai-avatar-img" />
            </div>
            <div class="thinking-text">
              思考中
              <span class="thinking-dot">●</span>
              <span class="thinking-dot">●</span>
              <span class="thinking-dot">●</span>
            </div>
          </div>
        </div>

        <!-- 输入框（有消息时显示在底部） -->
        <div v-if="messages.length > 0" class="input-wrapper-bottom">
          <div class="modern-input-container">
            <div class="input-left">
              <div class="add-btn-wrapper-bottom">
                <button class="add-btn" @click="toggleAddMenu" title="添加">
                  <svg
                    class="icon"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path d="M12 5v14M5 12h14" />
                  </svg>
                </button>

                <!-- 一级菜单 -->
                <div v-if="showAddMenu" class="add-menu-bottom">
                  <div class="menu-item" @click="openFileUpload">
                    <svg
                      class="menu-icon"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                    <span>上传文件</span>
                  </div>
                  <div class="menu-item" @click="openConfigDialog">
                    <svg
                      class="menu-icon"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <circle cx="12" cy="12" r="3" />
                      <path
                        d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
                      />
                    </svg>
                    <div class="menu-item-content">
                      <span>配置文件</span>
                      <span class="menu-subtitle">{{
                        selectedConfigName
                      }}</span>
                    </div>
                    <svg
                      class="menu-arrow"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </div>
                  <div class="menu-item stream-toggle" @click="toggleStream">
                    <svg
                      class="menu-icon"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <polygon
                        points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"
                      />
                    </svg>
                    <span>{{
                      streamEnabled ? "流式响应已开启" : "流式响应已关闭"
                    }}</span>
                  </div>
                </div>
              </div>
            </div>

            <textarea
              v-model="messageInput"
              :placeholder="currentPreset ? '输入消息...' : '请先选择预设方案'"
              @keydown="handleKeyPress"
              rows="1"
              class="modern-chat-input"
              :disabled="!currentPreset || isLoading"
            ></textarea>

            <div class="input-right">
              <button class="voice-btn" title="语音输入" :disabled="isLoading">
                <svg
                  class="icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"
                  />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              </button>
              <button
                class="send-btn-modern"
                @click="sendMessage"
                :disabled="!messageInput.trim() || isLoading || !currentPreset"
                title="发送"
              >
                <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 56px);
  background: var(--bg-primary);
  overflow: hidden;
  position: relative;
}

html.dark .chat-container {
  background: var(--bg-primary);
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

html.dark .sidebar {
  background: var(--bg-secondary);
}

.sidebar.collapsed {
  width: 60px;
  background: var(--bg-primary);
}

html.dark .sidebar.collapsed {
  background: var(--bg-primary);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 12px;
  flex-shrink: 0;
  min-height: 56px;
}

.collapse-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.collapse-btn .icon {
  width: 18px;
  height: 18px;
}

.sidebar-content {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
  opacity: 1;
  visibility: visible;
  transition:
    opacity 0.2s ease,
    visibility 0.2s ease;
  transition-delay: 0.15s;
}

.sidebar.collapsed .sidebar-content {
  opacity: 0;
  visibility: hidden;
  transition-delay: 0s;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 8px 0;
  background: transparent;
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 14px;
}

.new-chat-btn:hover {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.new-chat-btn.active {
  background: var(--primary-color-light, rgba(59, 130, 246, 0.1));
  color: var(--primary-color, #3b82f6);
}

.new-chat-btn .icon {
  width: 18px;
  height: 18px;
}

.chat-history {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-history-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding: 0 8px;
}

.chat-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  color: var(--text-secondary);
}

.chat-item-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.chat-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.chat-item.active {
  background: var(--primary-color-light, rgba(59, 130, 246, 0.1));
  color: var(--primary-color, #3b82f6);
}

.chat-item-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0.3;
  transition: opacity 0.2s;
}

.chat-item:hover .chat-item-actions {
  opacity: 1;
}

.chat-item.active .chat-item-actions {
  opacity: 1;
}

.chat-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.chat-title {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.chat-more-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.chat-more-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.chat-more-btn svg {
  width: 16px;
  height: 16px;
}

.chat-action-menu {
  position: fixed;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 6px;
  min-width: 160px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  color: var(--text-primary);
  font-size: 14px;
}

.menu-item:hover {
  background: var(--bg-hover);
}

.menu-item.danger {
  color: var(--error-color, #ef4444);
}

.menu-item.danger:hover {
  background: rgba(239, 68, 68, 0.1);
}

.menu-item svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.no-history {
  text-align: center;
  color: var(--text-placeholder);
  font-size: 13px;
  padding: 20px 8px;
}

/* 主聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 消息列表 */
.message-list {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: var(--bg-secondary);
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
  background: var(--primary-color);
  color: white;
}

.message.assistant {
  align-self: flex-start;
}

.message-content {
  flex: 1;
}

.message-text {
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-time {
  font-size: 12px;
  opacity: 0.7;
  margin-top: 8px;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.message-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-hover);
}

.message.user .message-avatar {
  background: rgba(255, 255, 255, 0.2);
}

.avatar-icon {
  width: 20px;
  height: 20px;
}

.avatar-icon.bot {
  width: 24px;
  height: 24px;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding-top: 280px;
  gap: 40px;
}

.welcome-text {
  text-align: center;
}

.welcome-text h1 {
  font-size: 32px;
  font-weight: 500;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 打字机效果 */
.typewriter {
  display: inline-block;
  position: relative;
  font-weight: 400;
}

:deep(.highlight) {
  font-family: "Dancing Script", cursive !important;
  font-weight: 700;
  font-size: 1.4em;
  color: #3b82f6;
}

.typewriter::after {
  content: "|";
  position: absolute;
  right: -8px;
  color: var(--text-primary);
  animation: blink 1s infinite;
}

/* 打字完成后隐藏光标 */
.empty-state:not(:hover) .typewriter::after {
  animation: none;
  opacity: 0;
}

@keyframes blink {
  0%,
  50% {
    opacity: 1;
  }
  51%,
  100% {
    opacity: 0;
  }
}

.welcome-icon {
  width: 32px;
  height: 32px;
  color: #409eff;
}

/* 空状态时的输入框（居中） */
.input-wrapper-center {
  width: 100%;
  max-width: 800px;
}

/* Markdown 预览容器 */
.markdown-preview-container {
  max-height: 300px;
  overflow-y: auto;
  padding: 12px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 8px;
}

/* 初始状态的输入框容器 - 大圆角椭圆，上下分层 */
.modern-input-container-center {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 32px;
  padding: 8px 8px 12px 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

html.dark .modern-input-container-center {
  background: rgb(45, 45, 45);
  border-color: #4a4a4a;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.modern-input-container-center:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

/* 上层：文本输入区域 */
.modern-chat-input-center {
  flex: 1;
  width: 100%;
  min-height: 60px;
  max-height: 300px;
  border: none;
  background: transparent;
  font-size: 16px;
  color: var(--text-primary);
  resize: none;
  outline: none;
  font-family: inherit;
  line-height: 1.5;
  padding: 24px 28px 12px 28px;
  border-radius: 24px;
}

.modern-chat-input-center::placeholder {
  color: #9ca3af;
}

.modern-chat-input-center:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 下层：按钮区域 */
.input-actions-center {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px 4px 16px;
}

.input-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 添加按钮 */
.add-btn-center {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #6b7280;
  flex-shrink: 0;
}

.add-btn-center:hover {
  background: #f3f4f6;
  color: #3b82f6;
}

html.dark .add-btn-center {
  color: #9ca3af;
}

html.dark .add-btn-center:hover {
  background: #374151;
  color: #60a5fa;
}

.add-btn-center .icon {
  width: 20px;
  height: 20px;
}

/* 添加按钮包装器 */
.add-btn-wrapper {
  position: relative;
}

.add-btn-wrapper-bottom {
  position: relative;
}

/* 一级菜单（初始状态） */
.add-menu {
  position: absolute;
  bottom: 48px;
  left: 0;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 240px;
  padding: 8px;
  z-index: 100;
  border: 1px solid #e5e7eb;
}

/* 一级菜单（底部状态） */
.add-menu-bottom {
  position: absolute;
  top: -200px;
  left: 0;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 240px;
  padding: 8px;
  z-index: 100;
  border: 1px solid #e5e7eb;
}

html.dark .add-menu {
  background: #1f2937;
  border-color: #374151;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

html.dark .add-menu-bottom {
  background: #1f2937;
  border-color: #374151;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  color: #374151;
}

html.dark .menu-item {
  color: #f9fafb;
}

.menu-item:hover {
  background: #f3f4f6;
}

html.dark .menu-item:hover {
  background: #374151;
}

.menu-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: #6b7280;
}

html.dark .menu-icon {
  color: #9ca3af;
}

.menu-item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-subtitle {
  font-size: 12px;
  color: #9ca3af;
}

html.dark .menu-subtitle {
  color: #6b7280;
}

.menu-arrow {
  width: 16px;
  height: 16px;
  color: #9ca3af;
}

.menu-item.stream-toggle {
  margin-top: 4px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

html.dark .menu-item.stream-toggle {
  border-top-color: #374151;
}

/* 配置文件弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.config-modal {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

html.dark .config-modal {
  background: #1f2937;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

html.dark .modal-header {
  border-bottom-color: #374151;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

html.dark .modal-header h2 {
  color: #f9fafb;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

html.dark .modal-close {
  color: #9ca3af;
}

html.dark .modal-close:hover {
  background: #374151;
  color: #f9fafb;
}

.modal-close svg {
  width: 20px;
  height: 20px;
}

.modal-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-item {
  padding: 14px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.config-item:hover {
  background: #f9fafb;
  border-color: #e5e7eb;
}

html.dark .config-item:hover {
  background: #374151;
  border-color: #4b5563;
}

.config-item.active {
  background: #eff6ff;
  border-color: #3b82f6;
}

html.dark .config-item.active {
  background: #1e3a5f;
  border-color: #60a5fa;
}

.config-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.config-item-name {
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
}

html.dark .config-item-name {
  color: #f9fafb;
}

.config-item-id {
  font-size: 12px;
  color: #9ca3af;
  font-family: monospace;
}

html.dark .config-item-id {
  color: #6b7280;
}

.check-icon {
  width: 20px;
  height: 20px;
  color: #3b82f6;
}

html.dark .check-icon {
  color: #60a5fa;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

html.dark .modal-footer {
  border-top-color: #374151;
}

.btn-cancel,
.btn-confirm {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-cancel {
  background: transparent;
  color: #6b7280;
}

.btn-cancel:hover {
  background: #f3f4f6;
  color: #1f2937;
}

html.dark .btn-cancel {
  color: #9ca3af;
}

html.dark .btn-cancel:hover {
  background: #374151;
  color: #f9fafb;
}

.btn-confirm {
  background: #3b82f6;
  color: white;
}

.btn-confirm:hover {
  background: #2563eb;
}

html.dark .btn-confirm {
  background: #60a5fa;
  color: #1f2937;
}

html.dark .btn-confirm:hover {
  background: #3b82f6;
}

/* 模型标签 */
.model-tag-center {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f3f4f6;
  border-radius: 9999px;
  font-size: 13px;
  color: #4b5563;
  font-weight: 500;
  flex-shrink: 0;
}

html.dark .model-tag-center {
  background: #374151;
  color: #e5e7eb;
}

.model-icon-center {
  width: 14px;
  height: 14px;
  color: #6b7280;
}

html.dark .model-icon-center {
  color: #9ca3af;
}

/* 语音按钮 */
.voice-btn-center {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #6b7280;
  flex-shrink: 0;
}

.voice-btn-center:hover {
  background: #f3f4f6;
  color: #3b82f6;
}

html.dark .voice-btn-center {
  color: #9ca3af;
}

html.dark .voice-btn-center:hover {
  background: #374151;
  color: #60a5fa;
}

.voice-btn-center:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.voice-btn-center .icon {
  width: 18px;
  height: 18px;
}

/* 发送按钮 */
.send-btn-center {
  width: 40px;
  height: 40px;
  border: none;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: white;
  flex-shrink: 0;
}

.send-btn-center:hover:not(:disabled) {
  background: #2563eb;
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.send-btn-center:active:not(:disabled) {
  transform: scale(0.95);
}

.send-btn-center:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  background: #9ca3af;
}

.send-btn-center .icon {
  width: 18px;
  height: 18px;
}

/* 输入框（有消息时固定在底部） */
.input-wrapper-bottom {
  position: fixed;
  bottom: 0;
  left: 280px;
  right: 0;
  padding: 16px 24px;
  background: var(--bg-primary, white);
  z-index: 100;
}

.sidebar.collapsed + .chat-main .input-wrapper-bottom {
  left: 60px;
}

.modern-input-container {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 12px 16px;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.05),
    0 2px 4px -1px rgba(0, 0, 0, 0.03);
  transition: all 0.2s;
}

html.dark .modern-input-container {
  background: rgb(45, 45, 45);
  border-color: #4a4a4a;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.3),
    0 2px 4px -1px rgba(0, 0, 0, 0.2);
}

.modern-input-container:focus-within {
  border-color: #3b82f6;
  box-shadow:
    0 4px 12px -1px rgba(59, 130, 246, 0.2),
    0 2px 6px -1px rgba(59, 130, 246, 0.1);
}

.input-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.add-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #6b7280;
  flex-shrink: 0;
}

.add-btn:hover {
  background: #f3f4f6;
  color: #3b82f6;
}

html.dark .add-btn:hover {
  background: #374151;
}

.add-btn .icon {
  width: 20px;
  height: 20px;
}

.model-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f3f4f6;
  border-radius: 20px;
  font-size: 13px;
  color: #4b5563;
  flex-shrink: 0;
}

html.dark .model-tag {
  background: #374151;
  color: #9ca3af;
}

.model-icon {
  width: 16px;
  height: 16px;
  color: #6b7280;
}

.modern-chat-input {
  flex: 1;
  min-height: 24px;
  max-height: 200px;
  padding: 8px 0;
  background: transparent;
  border: none;
  resize: none;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  color: var(--text-primary);
}

.modern-chat-input:focus {
  outline: none;
}

.modern-chat-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.input-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.voice-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #6b7280;
}

.voice-btn:hover:not(:disabled) {
  background: #f3f4f6;
  color: #3b82f6;
}

html.dark .voice-btn:hover:not(:disabled) {
  background: #374151;
}

.voice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.voice-btn .icon {
  width: 20px;
  height: 20px;
}

.send-btn-modern {
  width: 40px;
  height: 40px;
  border: none;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn-modern:hover:not(:disabled) {
  background: #2563eb;
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.send-btn-modern:active:not(:disabled) {
  transform: scale(0.95);
}

.send-btn-modern:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  background: #9ca3af;
}

.send-btn-modern .icon {
  width: 20px;
  height: 20px;
}

/* 配置菜单 */
.config-menu-wrapper {
  position: relative;
}

.config-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 8px;
  min-width: 220px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  color: var(--text-primary);
  position: relative;
}

.menu-item:hover {
  background: var(--bg-hover);
}

.menu-item.has-submenu:hover .submenu {
  display: block;
}

.menu-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--text-secondary);
}

.menu-text-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-text {
  font-size: 14px;
  font-weight: 500;
}

.menu-subtext {
  font-size: 12px;
  color: var(--text-secondary);
}

.menu-arrow {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

/* 子菜单 */
.submenu {
  display: none;
  position: absolute;
  left: calc(100% + 4px);
  top: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 8px;
  min-width: 200px;
  max-height: 300px;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 101;
}

.submenu-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.submenu-item:hover,
.submenu-item.active {
  background: var(--bg-hover);
}

.submenu-item.active .submenu-name {
  color: var(--primary-color);
}

.submenu-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.submenu-desc {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  padding-top: 0px;
  padding-bottom: 120px;
}

.message-wrapper {
  display: flex;
  width: 100%;
  margin-bottom: 12px;
  padding: 0 16px;
}

.message-wrapper.user {
  justify-content: flex-end;
}

.message-wrapper.assistant {
  justify-content: flex-start;
}

/* 用户消息 */
.user-message {
  max-width: 70%;
}

.message-bubble-user {
  padding: 10px 18px;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 400;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  background: #f3f4f6;
  color: #1f2937;
  display: inline-block;
}

html.dark .message-bubble-user {
  background: #374151;
  color: #f9fafb;
}

/* AI 消息 */
.assistant-message {
  display: flex;
  gap: 12px;
  max-width: 80%;
  align-items: flex-start;
  padding: 8px 0;
}

.assistant-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: -5px;
}

.ai-icon {
  width: 24px;
  height: 24px;
  color: #fbbf24;
}

.ai-avatar-img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  margin-top: 10px;
}

.assistant-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0px;
  margin-left: 8px;
}

.message-text-assistant {
  font-size: 16px;
  font-weight: 400;
  line-height: 1.8;
  word-break: break-word;
  color: #1f2937;
}

.message-text-assistant :deep(p) {
  margin-bottom: 0px;
}

.message-text-assistant :deep(p + p) {
  margin-top: 8px;
}

.message-text-assistant :deep(ol) {
  padding-left: 2em;
}

.message-text-assistant :deep(ul) {
  padding-left: 1.5em;
}

/* 标题间距 */
.message-text-assistant :deep(h1),
.message-text-assistant :deep(h2),
.message-text-assistant :deep(h3),
.message-text-assistant :deep(h4) {
  margin-top: 24px;
  margin-bottom: 12px;
}

/* 第一个标题不需要上边距 */
.message-text-assistant :deep(h1:first-child),
.message-text-assistant :deep(h2:first-child),
.message-text-assistant :deep(h3:first-child),
.message-text-assistant :deep(h4:first-child) {
  margin-top: 0;
}

/* 标题后面紧跟的段落或列表减少间距 */
.message-text-assistant :deep(h1 + p),
.message-text-assistant :deep(h2 + p),
.message-text-assistant :deep(h3 + p),
.message-text-assistant :deep(h4 + p),
.message-text-assistant :deep(h1 + ul),
.message-text-assistant :deep(h2 + ul),
.message-text-assistant :deep(h3 + ul),
.message-text-assistant :deep(h4 + ul),
.message-text-assistant :deep(h1 + ol),
.message-text-assistant :deep(h2 + ol),
.message-text-assistant :deep(h3 + ol),
.message-text-assistant :deep(h4 + ol) {
  margin-top: 8px;
}

html.dark .message-text-assistant {
  color: #f9fafb;
}

/* 深色模式代码块背景 */
html.dark .message-text-assistant :deep(pre.hljs) {
  background-color: #0d1117 !important;
}

/* 代码块样式 - 浅色模式背景 */
.message-text-assistant :deep(pre.hljs) {
  background-color: rgb(249, 250, 251) !important;
}

/* 代码块样式 - 给代码添加左边距 */
.message-text-assistant :deep(pre code) {
  display: block;
  padding-left: 16px !important;
}

/* 深色模式滚动条样式 - 全局 */
html.dark ::-webkit-scrollbar {
  width: 8px !important;
  height: 8px !important;
}

html.dark ::-webkit-scrollbar-track {
  background: #1f2937 !important;
}

html.dark ::-webkit-scrollbar-thumb {
  background: #4b5563 !important;
  border-radius: 4px !important;
}

html.dark ::-webkit-scrollbar-thumb:hover {
  background: #6b7280 !important;
}

/* 深色模式滚动条 - 特定容器 */
html.dark .sidebar-content::-webkit-scrollbar,
html.dark .chat-main::-webkit-scrollbar,
html.dark .message-list::-webkit-scrollbar {
  width: 8px !important;
  height: 8px !important;
}

html.dark .sidebar-content::-webkit-scrollbar-track,
html.dark .chat-main::-webkit-scrollbar-track,
html.dark .message-list::-webkit-scrollbar-track {
  background: #1f2937 !important;
}

html.dark .sidebar-content::-webkit-scrollbar-thumb,
html.dark .chat-main::-webkit-scrollbar-thumb,
html.dark .message-list::-webkit-scrollbar-thumb {
  background: #4b5563 !important;
  border-radius: 4px !important;
}

html.dark .sidebar-content::-webkit-scrollbar-thumb:hover,
html.dark .chat-main::-webkit-scrollbar-thumb:hover,
html.dark .message-list::-webkit-scrollbar-thumb:hover {
  background: #6b7280 !important;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--text-placeholder);
}

.message-time {
  color: var(--text-placeholder);
  font-size: 11px;
}

.message-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.assistant-content:hover .message-actions {
  opacity: 1;
}

.action-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-placeholder);
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f3f4f6;
  color: #3b82f6;
}

html.dark .action-btn:hover {
  background: #374151;
  color: #60a5fa;
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

/* 思考中状态 */
.thinking-text {
  font-size: 16px;
  font-weight: 400;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 6px;
}

html.dark .thinking-text {
  color: #f9fafb;
}

.thinking-dot {
  font-size: 16px;
  line-height: 1;
  animation: thinking-bounce 1.4s infinite ease-in-out both;
}

.thinking-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.thinking-dot:nth-child(2) {
  animation-delay: -0.16s;
}

.thinking-dot:nth-child(3) {
  animation-delay: 0s;
}

@keyframes thinking-bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.message-wrapper.assistant.loading {
  align-items: center;
}

.message-wrapper.assistant.loading .assistant-avatar {
  margin-top: 0;
}

.thinking-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.thinking-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes thinking-bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.thinking-text {
  font-size: 13px;
  color: var(--text-secondary);
}
</style>
