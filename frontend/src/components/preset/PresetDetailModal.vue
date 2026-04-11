<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { getPreset, type PresetDetail } from "../../api/preset";

interface Props {
  presetId: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
}>();

// 详情数据
const presetDetail = ref<PresetDetail | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

// 折叠面板状态
const expandedSections = ref({
  basic: true,
  model: true,
  prompt: true,
  memory: true,
  knowledgeBases: true,
  plugins: true,
  advanced: false,
});

// 加载预设详情
const loadPresetDetail = async () => {
  if (!props.presetId) return;

  loading.value = true;
  error.value = null;

  try {
    const response = await getPreset(props.presetId);
    presetDetail.value = response.data;
  } catch (err) {
    error.value = "加载预设详情失败";
    console.error("加载预设详情失败:", err);
  } finally {
    loading.value = false;
  }
};

// 切换折叠面板
const toggleSection = (section: keyof typeof expandedSections.value) => {
  expandedSections.value[section] = !expandedSections.value[section];
};

// 关闭弹窗
const handleClose = () => {
  emit("close");
};

// 监听presetId变化
watch(
  () => props.presetId,
  () => {
    loadPresetDetail();
  },
  { immediate: true },
);
</script>

<template>
  <div class="modal-overlay" @click="handleClose">
    <div class="modal-content" @click.stop>
      <!-- 弹窗头部 -->
      <div class="modal-header">
        <h2 class="modal-title">预设方案详情</h2>
        <button class="modal-close" @click="handleClose">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
            />
          </svg>
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <span>加载中...</span>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="error-state">
        <span>{{ error }}</span>
      </div>

      <!-- 详情内容 -->
      <div v-else-if="presetDetail" class="modal-body">
        <!-- 基础信息 -->
        <div class="section-panel">
          <div class="section-header" @click="toggleSection('basic')">
            <h3 class="section-title">基础信息</h3>
            <svg
              class="expand-icon"
              :class="{ rotated: !expandedSections.basic }"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" />
            </svg>
          </div>
          <div v-if="expandedSections.basic" class="section-content">
            <div class="info-grid">
              <div class="info-item">
                <label>预设ID</label>
                <span class="info-value">{{ presetDetail.preset_id }}</span>
              </div>
              <div class="info-item">
                <label>预设名称</label>
                <span class="info-value">{{ presetDetail.preset_name }}</span>
              </div>
              <div class="info-item">
                <label>描述</label>
                <span class="info-value">{{
                  presetDetail.description || "暂无描述"
                }}</span>
              </div>
              <div class="info-item">
                <label>状态</label>
                <span
                  class="status-badge"
                  :class="{
                    active: presetDetail.is_active,
                    inactive: !presetDetail.is_active,
                  }"
                >
                  {{ presetDetail.is_active ? "启用" : "禁用" }}
                </span>
              </div>
              <div class="info-item">
                <label>默认预设</label>
                <span
                  class="status-badge"
                  :class="{ default: presetDetail.is_default }"
                >
                  {{ presetDetail.is_default ? "是" : "否" }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 模型配置 -->
        <div class="section-panel" v-if="presetDetail.model_info">
          <div class="section-header" @click="toggleSection('model')">
            <h3 class="section-title">模型配置</h3>
            <svg
              class="expand-icon"
              :class="{ rotated: !expandedSections.model }"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" />
            </svg>
          </div>
          <div v-if="expandedSections.model" class="section-content">
            <div class="info-grid">
              <div class="info-item">
                <label>模型名称</label>
                <span class="info-value">{{
                  presetDetail.model_info.model_name.join(", ")
                }}</span>
              </div>
              <div class="info-item">
                <label>模型类型</label>
                <span class="info-value">{{
                  presetDetail.model_info.model_type
                }}</span>
              </div>
              <div class="info-item">
                <label>提供商</label>
                <span class="info-value">{{
                  presetDetail.model_info.provider
                }}</span>
              </div>
              <div class="info-item" v-if="presetDetail.model_info.api_base">
                <label>API地址</label>
                <span class="info-value code">{{
                  presetDetail.model_info.api_base
                }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 提示词配置 -->
        <div class="section-panel" v-if="presetDetail.prompt_info">
          <div class="section-header" @click="toggleSection('prompt')">
            <h3 class="section-title">提示词配置</h3>
            <svg
              class="expand-icon"
              :class="{ rotated: !expandedSections.prompt }"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" />
            </svg>
          </div>
          <div v-if="expandedSections.prompt" class="section-content">
            <div class="info-grid">
              <div class="info-item">
                <label>提示词名称</label>
                <span class="info-value">{{
                  presetDetail.prompt_info.prompt_name
                }}</span>
              </div>
              <div class="info-item full-width">
                <label>系统提示词</label>
                <div class="system-prompt">
                  {{ presetDetail.prompt_info.system_prompt }}
                </div>
              </div>
              <div
                class="info-item"
                v-if="presetDetail.prompt_info.variables?.length"
              >
                <label>变量</label>
                <span class="info-value">{{
                  presetDetail.prompt_info.variables.join(", ")
                }}</span>
              </div>
              <div
                class="info-item"
                v-if="presetDetail.prompt_info.temperature_override"
              >
                <label>温度覆盖</label>
                <span class="info-value">{{
                  presetDetail.prompt_info.temperature_override
                }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 记忆配置 -->
        <div class="section-panel" v-if="presetDetail.memory_info">
          <div class="section-header" @click="toggleSection('memory')">
            <h3 class="section-title">记忆配置</h3>
            <svg
              class="expand-icon"
              :class="{ rotated: !expandedSections.memory }"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" />
            </svg>
          </div>
          <div v-if="expandedSections.memory" class="section-content">
            <div class="info-grid">
              <div class="info-item">
                <label>记忆名称</label>
                <span class="info-value">{{
                  presetDetail.memory_info.memory_name
                }}</span>
              </div>
              <div class="info-item">
                <label>记忆类型</label>
                <span class="info-value">{{
                  presetDetail.memory_info.memory_type
                }}</span>
              </div>
              <div
                class="info-item full-width"
                v-if="presetDetail.memory_info.memory_params"
              >
                <label>参数配置</label>
                <pre class="json-code">{{
                  JSON.stringify(
                    presetDetail.memory_info.memory_params,
                    null,
                    2,
                  )
                }}</pre>
              </div>
            </div>
          </div>
        </div>

        <!-- 知识库配置 -->
        <div
          class="section-panel"
          v-if="presetDetail.knowledge_bases_info?.length"
        >
          <div class="section-header" @click="toggleSection('knowledgeBases')">
            <h3 class="section-title">
              知识库配置 ({{ presetDetail.knowledge_bases_info.length }})
            </h3>
            <svg
              class="expand-icon"
              :class="{ rotated: !expandedSections.knowledgeBases }"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" />
            </svg>
          </div>
          <div v-if="expandedSections.knowledgeBases" class="section-content">
            <div
              v-for="kb in presetDetail.knowledge_bases_info"
              :key="kb.kb_id"
              class="kb-item"
            >
              <div class="kb-header">
                <h4 class="kb-name">{{ kb.kb_name }}</h4>
                <span class="kb-id">{{ kb.kb_id }}</span>
              </div>
              <div class="kb-details">
                <span class="kb-info">文档数: {{ kb.document_count }}</span>
                <span class="kb-info">分块数: {{ kb.total_chunks }}</span>
                <span class="kb-info">嵌入模型: {{ kb.embedding_model }}</span>
              </div>
              <p v-if="kb.description" class="kb-description">
                {{ kb.description }}
              </p>
            </div>
          </div>
        </div>

        <!-- 插件配置 -->
        <div class="section-panel" v-if="presetDetail.plugins_info?.length">
          <div class="section-header" @click="toggleSection('plugins')">
            <h3 class="section-title">
              插件配置 ({{ presetDetail.plugins_info.length }})
            </h3>
            <svg
              class="expand-icon"
              :class="{ rotated: !expandedSections.plugins }"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" />
            </svg>
          </div>
          <div v-if="expandedSections.plugins" class="section-content">
            <div
              v-for="plugin in presetDetail.plugins_info"
              :key="plugin.plugin_id"
              class="plugin-item"
            >
              <div class="plugin-header">
                <h4 class="plugin-name">{{ plugin.plugin_name }}</h4>
                <span class="plugin-id">{{ plugin.plugin_id }}</span>
              </div>
              <div class="plugin-details">
                <span class="plugin-info">类名: {{ plugin.class_name }}</span>
                <span class="plugin-info" v-if="plugin.module_path"
                  >模块路径: {{ plugin.module_path }}</span
                >
              </div>
            </div>
          </div>
        </div>

        <!-- 高级配置 -->
        <div
          class="section-panel"
          v-if="presetDetail.overrides || presetDetail.channel_config"
        >
          <div class="section-header" @click="toggleSection('advanced')">
            <h3 class="section-title">高级配置</h3>
            <svg
              class="expand-icon"
              :class="{ rotated: !expandedSections.advanced }"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" />
            </svg>
          </div>
          <div v-if="expandedSections.advanced" class="section-content">
            <div class="info-grid">
              <div class="info-item full-width" v-if="presetDetail.overrides">
                <label>覆盖配置</label>
                <pre class="json-code">{{
                  JSON.stringify(presetDetail.overrides, null, 2)
                }}</pre>
              </div>
              <div
                class="info-item full-width"
                v-if="presetDetail.channel_config"
              >
                <label>渠道配置</label>
                <pre class="json-code">{{
                  JSON.stringify(presetDetail.channel_config, null, 2)
                }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
}

.modal-content {
  background: var(--bg-primary);
  border-radius: 12px;
  width: 90vw;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow:
    0 20px 25px -5px rgba(0, 0, 0, 0.1),
    0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.modal-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.modal-close svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
}

.loading-state,
.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-tertiary);
}

.error-state {
  color: #ef4444;
}

/* 折叠面板样式 */
.section-panel {
  margin-top: 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.section-panel:first-child {
  margin-top: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--bg-secondary);
  cursor: pointer;
  transition: background 0.2s;
}

.section-header:hover {
  background: var(--bg-hover);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.expand-icon {
  width: 20px;
  height: 20px;
  transition: transform 0.2s;
  color: var(--text-secondary);
}

.expand-icon.rotated {
  transform: rotate(-90deg);
}

.section-content {
  padding: 16px;
  background: var(--bg-primary);
}

/* 信息网格布局 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-item label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.info-value.code {
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  background: var(--bg-secondary);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

/* 状态徽章 */
.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: #dcfce7;
  color: #166534;
}

.status-badge.inactive {
  background: #f3f4f6;
  color: #6b7280;
}

.status-badge.default {
  background: #dbeafe;
  color: #1e40af;
}

/* 系统提示词样式 */
.system-prompt {
  background: var(--bg-secondary);
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

/* JSON代码样式 */
.json-code {
  background: var(--bg-secondary);
  padding: 12px;
  border-radius: 6px;
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-primary);
  overflow-x: auto;
  white-space: pre;
}

/* 知识库和插件项样式 */
.kb-item,
.plugin-item {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  margin-bottom: 8px;
}

.kb-item:last-child,
.plugin-item:last-child {
  margin-bottom: 0;
}

.kb-header,
.plugin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.kb-name,
.plugin-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.kb-id,
.plugin-id {
  font-size: 11px;
  color: var(--text-tertiary);
  font-family: monospace;
}

.kb-details,
.plugin-details {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.kb-info,
.plugin-info {
  font-size: 12px;
  color: var(--text-secondary);
}

.kb-description {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
  line-height: 1.4;
}
</style>
