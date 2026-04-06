<script setup lang="ts">
import { ref, computed } from "vue";
import { t } from "../../../locales";
import ChatModelConfig from "../../../components/model-provider/ChatModelConfig.vue";
import EmbeddingModelConfig from "../../../components/model-provider/EmbeddingModelConfig.vue";

const $t = computed(() => t);

// 当前激活的标签页
const activeTab = ref("chat");

// 标签页配置
const tabs = [
  {
    key: "chat",
    label: computed(() => $t.value("provider.tabs.chat") || "对话"),
    icon: "chat",
  },
  {
    key: "agent",
    label: computed(() => $t.value("provider.tabs.agent") || "Agent 执行器"),
    icon: "agent",
  },
  {
    key: "stt",
    label: computed(() => $t.value("provider.tabs.stt") || "语音转文字"),
    icon: "stt",
  },
  {
    key: "tts",
    label: computed(() => $t.value("provider.tabs.tts") || "文字转语音"),
    icon: "tts",
  },
  {
    key: "embedding",
    label: computed(
      () => $t.value("provider.tabs.embedding") || "嵌入(Embedding)",
    ),
    icon: "embedding",
  },
  {
    key: "rerank",
    label: computed(() => $t.value("provider.tabs.rerank") || "重排序(Rerank)"),
    icon: "rerank",
  },
];

// 切换标签页
const switchTab = (key: string) => {
  activeTab.value = key;
};

// 获取图标SVG
const getIconSvg = (icon: string) => {
  const icons: Record<string, string> = {
    chat: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>`,
    agent: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/></svg>`,
    stt: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>`,
    tts: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>`,
    embedding: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`,
    rerank: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>`,
  };
  return icons[icon] || icons.chat;
};
</script>

<template>
  <div class="model-provider-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="title-with-icon">
        <svg class="header-icon" viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"
          />
        </svg>
        <h1 class="page-title">{{ $t("provider.title") || "模型提供商" }}</h1>
      </div>
      <p class="page-description">
        {{ $t("provider.description") || "管理和配置您的 AI 模型提供商" }}
      </p>
    </div>

    <!-- 标签页 -->
    <div class="tabs-container">
      <div
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        <span class="tab-icon" v-html="getIconSvg(tab.icon)"></span>
        <span class="tab-label">{{ tab.label }}</span>
      </div>
    </div>

    <!-- 内容区域 - 使用组件 -->
    <div class="content-area">
      <!-- 对话模型配置 -->
      <ChatModelConfig v-if="activeTab === 'chat'" />

      <!-- 嵌入模型配置 -->
      <EmbeddingModelConfig v-else-if="activeTab === 'embedding'" />

      <!-- 其他模型类型占位 -->
      <div v-else class="placeholder-content">
        <svg class="placeholder-icon" viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"
          />
        </svg>
        <p class="placeholder-text">
          {{ $t("provider.comingSoon") || "功能开发中..." }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.model-provider-view {
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 页面标题 */
.page-header {
  margin-bottom: 24px;
  flex-shrink: 0;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.header-icon {
  width: 32px;
  height: 32px;
  color: var(--primary-color);
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.page-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* 标签页 */
.tabs-container {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 12px;
  flex-shrink: 0;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  border: 1px solid transparent;
}

.tab-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.tab-item.active {
  background: var(--primary-light);
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.tab-icon {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tab-icon svg {
  width: 100%;
  height: 100%;
}

/* 内容区域 */
.content-area {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

/* 占位内容 */
.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: var(--bg-secondary);
  border-radius: 12px;
  color: var(--text-tertiary);
}

.placeholder-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.placeholder-text {
  font-size: 14px;
}
</style>
