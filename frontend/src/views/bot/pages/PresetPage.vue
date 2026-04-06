<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { t } from "../../../locales";
import {
  getPresets,
  deletePreset,
  type PresetListItem,
} from "../../../api/preset";

const $t = computed(() => t);

const presets = ref<PresetListItem[]>([]);
const loading = ref(false);
const searchKeyword = ref("");

// 加载预设方案列表
const loadPresets = async () => {
  loading.value = true;
  try {
    const response = await getPresets();
    presets.value = response.data || [];
  } catch (error) {
    console.error("加载预设方案失败:", error);
  } finally {
    loading.value = false;
  }
};

// 删除预设方案
const handleDelete = async (presetId: string) => {
  if (!confirm("确定要删除这个预设方案吗？")) return;
  try {
    await deletePreset(presetId);
    await loadPresets();
  } catch (error) {
    console.error("删除预设方案失败:", error);
  }
};

// 过滤后的预设方案列表
const filteredPresets = computed(() => {
  if (!searchKeyword.value) return presets.value;
  const keyword = searchKeyword.value.toLowerCase();
  return presets.value.filter(
    (p) =>
      p.preset_name.toLowerCase().includes(keyword) ||
      (p.description?.toLowerCase() || "").includes(keyword),
  );
});

onMounted(() => {
  loadPresets();
});
</script>

<template>
  <div class="preset-page">
    <div class="page-header">
      <h1>{{ $t("bot.preset.title") || "预设方案" }}</h1>
      <p>
        {{ $t("bot.preset.subtitle") || "组合资源池配置，快速搭建 AI 智能体" }}
      </p>
    </div>

    <div class="page-content">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="search-box">
          <svg class="search-icon" viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"
            />
          </svg>
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索预设方案..."
          />
        </div>
        <button class="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
          </svg>
          {{ $t("bot.preset.create") || "创建预设方案" }}
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <span>加载中...</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="filteredPresets.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z"
          />
        </svg>
        <span>暂无预设方案，点击"创建预设方案"添加</span>
      </div>

      <!-- 预设方案列表 -->
      <div v-else class="preset-grid">
        <div
          v-for="preset in filteredPresets"
          :key="preset.preset_id"
          class="preset-card"
          :class="{ 'is-inactive': !preset.is_active }"
        >
          <div class="card-header">
            <h3 class="card-title">{{ preset.preset_name }}</h3>
            <div class="card-badges">
              <span v-if="preset.is_default" class="badge badge-default"
                >默认</span
              >
              <span v-if="!preset.is_active" class="badge badge-inactive"
                >已禁用</span
              >
            </div>
            <button
              v-if="!preset.is_default"
              class="card-delete-btn"
              @click="handleDelete(preset.preset_id)"
              title="删除"
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path
                  d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"
                />
              </svg>
            </button>
          </div>

          <div class="card-body">
            <p class="card-description">
              {{ preset.description || "暂无描述" }}
            </p>

            <!-- 资源引用摘要 -->
            <div class="resource-summary">
              <div class="resource-item" v-if="preset.model_name">
                <span class="resource-label">模型:</span>
                <span class="resource-value">{{ preset.model_name }}</span>
              </div>
              <div class="resource-item" v-if="preset.prompt_name">
                <span class="resource-label">人设:</span>
                <span class="resource-value">{{ preset.prompt_name }}</span>
              </div>
              <div class="resource-item" v-if="preset.plugin_names?.length">
                <span class="resource-label">插件:</span>
                <span class="resource-value"
                  >{{ preset.plugin_names.length }} 个</span
                >
              </div>
              <div
                class="resource-item"
                v-if="preset.knowledge_base_names?.length"
              >
                <span class="resource-label">知识库:</span>
                <span class="resource-value"
                  >{{ preset.knowledge_base_names.length }} 个</span
                >
              </div>
            </div>
          </div>

          <div class="card-footer">
            <span class="card-id">ID: {{ preset.preset_id }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.preset-page {
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
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 320px;
}

.search-box .search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
}

.search-box input {
  width: 100%;
  padding: 8px 12px 8px 36px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  background: var(--bg-primary);
  color: var(--text-primary);
  outline: none;
  transition: all 0.2s;
}

.search-box input:focus {
  border-color: var(--primary-color);
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
  background: rgb(236, 245, 255);
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
}

.btn-primary:hover {
  background: rgb(220, 238, 255);
  color: var(--primary-color);
}

/* 深色模式按钮 */
html.dark .btn-primary {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border-color: #3b82f6;
}

html.dark .btn-primary:hover {
  background: rgba(59, 130, 246, 0.25);
  color: #60a5fa;
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

.preset-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
  align-content: start;
}

.preset-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
  cursor: pointer;
}

.preset-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: var(--primary-color);
}

.preset-card.is-inactive {
  opacity: 0.7;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  flex: 1;
}

.card-badges {
  display: flex;
  gap: 6px;
}

.badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.badge-default {
  background: var(--primary-color);
  color: white;
}

.badge-inactive {
  background: #f5f5f5;
  color: #999;
}

.card-delete-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.card-delete-btn:hover {
  background: var(--bg-hover);
  color: #ff4d4f;
}

.card-delete-btn svg {
  width: 18px;
  height: 18px;
}

.card-body {
  flex: 1;
}

.card-description {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 16px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.resource-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resource-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.resource-label {
  color: var(--text-tertiary);
  min-width: 48px;
}

.resource-value {
  color: var(--text-secondary);
  font-weight: 500;
}

.card-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.card-id {
  font-size: 11px;
  color: var(--text-tertiary);
  font-family: monospace;
}
</style>
