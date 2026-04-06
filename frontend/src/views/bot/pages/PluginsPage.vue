<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { t } from "../../../locales";

const $t = computed(() => t);

const loading = ref(false);
const plugins = ref([]);

const loadPlugins = async () => {
  loading.value = true;
  try {
    // TODO: 调用 API 获取插件列表
    console.log("加载插件列表");
  } catch (error) {
    console.error("加载插件失败:", error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadPlugins();
});
</script>

<template>
  <div class="plugins-page">
    <div class="page-header">
      <h1>{{ $t("bot.plugins.title") || "插件管理" }}</h1>
      <p>{{ $t("bot.plugins.subtitle") || "管理 MCP 插件资源" }}</p>
    </div>

    <div class="page-content">
      <div class="toolbar">
        <button class="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
          </svg>
          {{ $t("bot.plugins.create") || "添加插件" }}
        </button>
      </div>

      <div v-if="loading" class="loading-state">
        <span>加载中...</span>
      </div>

      <div v-else-if="plugins.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"
          />
        </svg>
        <span>暂无插件，点击"添加插件"添加</span>
      </div>

      <div v-else class="plugins-list">
        <!-- 插件列表 -->
      </div>
    </div>
  </div>
</template>

<style scoped>
.plugins-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px 32px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.page-header p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.page-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn svg {
  width: 16px;
  height: 16px;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
}

.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  gap: 12px;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  opacity: 0.5;
}

.empty-state span {
  font-size: 14px;
}
</style>
