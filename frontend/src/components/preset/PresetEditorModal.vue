<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { t } from "../../locales";
import {
  getPreset,
  createPreset,
  updatePreset,
  type PresetDetail,
  type PresetCreate,
  type PresetUpdate,
} from "../../api/preset";
import {
  getModelConfigs,
  type ModelConfigListItem,
} from "../../api/modelConfig";
import {
  getPromptConfigList,
  type PromptConfigListItem,
} from "../../api/promptConfig";

const $t = computed(() => t);

interface Props {
  presetId?: string;
  isOpen: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  success: [];
}>();

// 表单数据
const formData = ref<Partial<PresetDetail>>({
  preset_id: "",
  preset_name: "",
  description: "",
  selected_model: "",
  selected_prompt: undefined,
  selected_memory: undefined,
  selected_plugins: [],
  selected_knowledge_bases: [],
  overrides: {},
  channel_config: {
    enable_web: true,
    enable_feishu: false,
    enable_dingtalk: false,
    enable_telegram: false,
  },
  is_default: false,
  is_active: true,
});

// 模型提供商列表
const modelConfigs = ref<ModelConfigListItem[]>([]);
// 扁平化的模型列表
const flatModels = ref<{ model_name: string; provider: string }[]>([]);
// 提示词配置列表
const promptConfigs = ref<PromptConfigListItem[]>([]);
const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);

// 表单验证
const formErrors = ref<Record<string, string>>({});

// 折叠状态
const expandedSections = ref<Record<string, boolean>>({
  basic: true,
  model: true,
  prompt: true,
  memory: true,
  knowledgeBase: true,
  plugin: true,
  advanced: false,
});

// 加载模型提供商列表
const loadModelConfigs = async () => {
  try {
    const response = await getModelConfigs("chat");
    modelConfigs.value = response.data || [];

    // 将所有模型扁平化为一个列表
    flatModels.value = [];
    for (const config of modelConfigs.value) {
      for (const model_name of config.model_name) {
        flatModels.value.push({
          model_name: model_name,
          provider: config.provider,
        });
      }
    }
  } catch (err) {
    console.error("加载模型提供商失败:", err);
  }
};

// 加载提示词配置列表
const loadPromptConfigs = async () => {
  try {
    const response = await getPromptConfigList();
    promptConfigs.value = response.data || [];
  } catch (err) {
    console.error("加载提示词配置失败:", err);
  }
};

// 加载预设详情
const loadPresetDetail = async () => {
  if (!props.presetId) return;

  loading.value = true;
  error.value = null;

  try {
    const response = await getPreset(props.presetId);
    formData.value = response.data;
  } catch (err) {
    error.value = $t("bot.preset.loadDetailFailed");
    console.error("加载预设详情失败:", err);
  } finally {
    loading.value = false;
  }
};

// 表单验证
const validateForm = (): boolean => {
  formErrors.value = {};

  if (!formData.value.preset_name?.trim()) {
    formErrors.value.preset_name = $t("bot.preset.nameRequired");
  }

  if (!formData.value.selected_model) {
    formErrors.value.selected_model = $t("bot.preset.modelRequired");
  }

  if (Object.keys(formErrors.value).length > 0) {
    return false;
  }

  return true;
};

// 保存预设
const savePreset = async () => {
  if (!validateForm()) return;

  saving.value = true;
  error.value = null;

  try {
    if (props.presetId) {
      // 更新预设
      const updateData: PresetUpdate = {
        preset_name: formData.value.preset_name,
        description: formData.value.description,
        selected_model: formData.value.selected_model,
        selected_prompt: formData.value.selected_prompt,
        selected_memory: formData.value.selected_memory,
        selected_plugins: formData.value.selected_plugins,
        selected_knowledge_bases: formData.value.selected_knowledge_bases,
        overrides: formData.value.overrides,
        channel_config: formData.value.channel_config,
        is_default: formData.value.is_default,
        is_active: formData.value.is_active,
      };

      await updatePreset(props.presetId, updateData);
    } else {
      // 创建预设
      const createData: PresetCreate = {
        preset_id: formData.value.preset_id || "",
        preset_name: formData.value.preset_name!,
        description: formData.value.description,
        selected_model: formData.value.selected_model!,
        selected_prompt: formData.value.selected_prompt,
        selected_memory: formData.value.selected_memory,
        selected_plugins: formData.value.selected_plugins,
        selected_knowledge_bases: formData.value.selected_knowledge_bases,
        overrides: formData.value.overrides,
        channel_config: formData.value.channel_config,
        is_default: formData.value.is_default || false,
        is_active: formData.value.is_active ?? true,
      };

      await createPreset(createData);
    }

    emit("success");
  } catch (err) {
    error.value = props.presetId
      ? $t("bot.preset.updateFailed")
      : $t("bot.preset.createFailed");
    console.error(props.presetId ? "更新预设失败:" : "创建预设失败:", err);
  } finally {
    saving.value = false;
  }
};

// 关闭弹窗
const handleClose = () => {
  emit("close");
};

// 切换折叠状态
const toggleSection = (section: string) => {
  expandedSections.value[section] = !expandedSections.value[section];
};

// 格式化JSON
const formatJson = (data: any): string => {
  if (!data) return "{}";
  return JSON.stringify(data, null, 2);
};

// 监听弹窗打开状态
watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      if (props.presetId) {
        loadPresetDetail();
      } else {
        // 清空表单
        formData.value = {
          preset_id: "",
          preset_name: "",
          description: "",
          selected_model: "",
          selected_prompt: undefined,
          selected_memory: undefined,
          selected_plugins: [],
          selected_knowledge_bases: [],
          overrides: {},
          channel_config: {
            enable_web: true,
            enable_feishu: false,
            enable_dingtalk: false,
            enable_telegram: false,
          },
          is_default: false,
          is_active: true,
        };
      }
      loadModelConfigs();
      loadPromptConfigs();
    }
  },
  { immediate: true },
);

// 监听presetId变化
watch(
  () => props.presetId,
  () => {
    if (props.isOpen && props.presetId) {
      loadPresetDetail();
    }
  },
);
</script>

<template>
  <div class="modal-overlay" @click="handleClose">
    <div class="modal-content modal-content-large" @click.stop>
      <!-- 弹窗头部 -->
      <div class="modal-header">
        <h2 class="modal-title">
          {{ presetId ? $t("bot.preset.edit") : $t("bot.preset.create") }}
        </h2>
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
        <span>{{ $t("common.loading") }}</span>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="error-state">
        <span>{{ error }}</span>
      </div>

      <!-- 表单内容 -->
      <div v-else class="modal-body">
        <form class="preset-form" @submit.prevent="savePreset">
          <!-- 1. 基础信息 -->
          <div class="section-panel">
            <div class="section-header" @click="toggleSection('basic')">
              <div class="section-title-wrapper">
                <h3 class="section-title">{{ $t("bot.preset.basicInfo") }}</h3>
              </div>
              <div class="section-header-actions">
                <span class="section-badge" v-if="formData.preset_id"
                  >ID: {{ formData.preset_id }}</span
                >
                <span
                  class="collapse-icon"
                  :class="{ rotated: expandedSections.basic }"
                >
                  ▶
                </span>
              </div>
            </div>
            <div
              class="section-content"
              :class="{ expanded: expandedSections.basic }"
            >
              <div class="form-row">
                <div class="form-group">
                  <label for="preset_id">{{ $t("bot.preset.id") }}</label>
                  <input
                    id="preset_id"
                    v-model="formData.preset_id"
                    type="text"
                    :placeholder="$t('bot.preset.idHint')"
                    :disabled="!!presetId"
                  />
                  <span v-if="formErrors.preset_id" class="form-error">{{
                    formErrors.preset_id
                  }}</span>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="preset_name">{{ $t("bot.preset.name") }}</label>
                  <input
                    id="preset_name"
                    v-model="formData.preset_name"
                    type="text"
                    :placeholder="$t('bot.preset.nameHint')"
                  />
                  <span v-if="formErrors.preset_name" class="form-error">{{
                    formErrors.preset_name
                  }}</span>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="description">{{
                    $t("bot.preset.description")
                  }}</label>
                  <textarea
                    id="description"
                    v-model="formData.description"
                    rows="3"
                    :placeholder="$t('bot.preset.descriptionHint')"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- 2. 模型配置 -->
          <div class="section-panel">
            <div class="section-header" @click="toggleSection('model')">
              <div class="section-title-wrapper">
                <h3 class="section-title">
                  {{ $t("bot.preset.modelConfig") }}
                </h3>
              </div>
              <div class="section-header-actions">
                <span
                  class="section-badge"
                  v-if="formData.model_info?.provider"
                >
                  {{ formData.model_info.provider }}
                </span>
                <span
                  class="collapse-icon"
                  :class="{ rotated: expandedSections.model }"
                >
                  ▶
                </span>
              </div>
            </div>
            <div
              class="section-content"
              :class="{ expanded: expandedSections.model }"
            >
              <div class="form-row">
                <div class="form-group">
                  <label for="selected_model">{{
                    $t("bot.preset.model")
                  }}</label>
                  <select id="selected_model" v-model="formData.selected_model">
                    <option value="" disabled>
                      {{ $t("bot.preset.selectModel") }}
                    </option>
                    <option
                      v-for="model in flatModels"
                      :key="model.model_name"
                      :value="model.model_name"
                    >
                      {{ model.provider }} - {{ model.model_name }}
                    </option>
                  </select>
                  <span v-if="formErrors.selected_model" class="form-error">{{
                    formErrors.selected_model
                  }}</span>
                </div>
              </div>

              <!-- 模型详情（只读展示） -->
              <div v-if="formData.model_info" class="info-grid">
                <div class="info-item">
                  <label>{{ $t("bot.preset.modelId") }}</label>
                  <span class="info-value">{{
                    formData.model_info.model_id
                  }}</span>
                </div>
                <div class="info-item">
                  <label>{{ $t("bot.preset.modelType") }}</label>
                  <span class="info-value">{{
                    formData.model_info.model_type
                  }}</span>
                </div>
                <div class="info-item">
                  <label>{{ $t("bot.preset.provider") }}</label>
                  <span class="info-value">{{
                    formData.model_info.provider
                  }}</span>
                </div>
                <div class="info-item" v-if="formData.model_info.api_base">
                  <label>{{ $t("bot.preset.apiAddress") }}</label>
                  <span class="info-value code">{{
                    formData.model_info.api_base
                  }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 3. 提示词配置 -->
          <div class="section-panel">
            <div class="section-header" @click="toggleSection('prompt')">
              <div class="section-title-wrapper">
                <h3 class="section-title">
                  {{ $t("bot.preset.promptConfig") }}
                </h3>
              </div>
              <div class="section-header-actions">
                <span
                  class="section-badge"
                  v-if="formData.prompt_info?.prompt_name"
                >
                  {{ formData.prompt_info.prompt_name }}
                </span>
                <span
                  class="collapse-icon"
                  :class="{ rotated: expandedSections.prompt }"
                >
                  ▶
                </span>
              </div>
            </div>
            <div
              class="section-content"
              :class="{ expanded: expandedSections.prompt }"
            >
              <div class="form-row">
                <div class="form-group">
                  <label for="selected_prompt">{{
                    $t("bot.preset.promptName")
                  }}</label>
                  <select
                    id="selected_prompt"
                    v-model="formData.selected_prompt"
                  >
                    <option value="" disabled>
                      {{ $t("bot.preset.selectPrompt") || "请选择提示词" }}
                    </option>
                    <option
                      v-for="prompt in promptConfigs"
                      :key="prompt.prompt_id"
                      :value="prompt.prompt_id"
                    >
                      {{ prompt.prompt_name }}
                    </option>
                  </select>
                </div>
              </div>

              <div v-if="formData.prompt_info" class="info-grid">
                <div class="info-item">
                  <label>{{ $t("bot.preset.promptName") }}</label>
                  <span class="info-value">{{
                    formData.prompt_info.prompt_name
                  }}</span>
                </div>
                <div
                  class="info-item"
                  v-if="formData.prompt_info.temperature_override !== undefined"
                >
                  <label>{{ $t("bot.preset.temperatureOverride") }}</label>
                  <span class="info-value">{{
                    formData.prompt_info.temperature_override
                  }}</span>
                </div>
              </div>
              <div
                v-if="formData.prompt_info?.system_prompt"
                class="info-group"
              >
                <label>{{ $t("bot.preset.systemPrompt") }}</label>
                <div class="info-value system-prompt">
                  {{ formData.prompt_info.system_prompt }}
                </div>
              </div>
              <div
                v-if="formData.prompt_info?.variables?.length"
                class="info-group"
              >
                <label>{{ $t("bot.preset.variables") }}</label>
                <div class="info-value">
                  <span
                    v-for="variable in formData.prompt_info.variables"
                    :key="variable"
                    class="tag"
                  >
                    {{ variable }}
                  </span>
                </div>
              </div>
              <div v-else-if="!formData.prompt_info" class="info-empty">
                {{ $t("bot.preset.noPromptConfig") }}
              </div>
            </div>
          </div>

          <!-- 4. 记忆配置 -->
          <div class="section-panel">
            <div class="section-header" @click="toggleSection('memory')">
              <div class="section-title-wrapper">
                <h3 class="section-title">
                  {{ $t("bot.preset.memoryConfig") }}
                </h3>
              </div>
              <div class="section-header-actions">
                <span
                  class="section-badge"
                  v-if="formData.memory_info?.memory_name"
                >
                  {{ formData.memory_info.memory_name }}
                </span>
                <span
                  class="collapse-icon"
                  :class="{ rotated: expandedSections.memory }"
                >
                  ▶
                </span>
              </div>
            </div>
            <div
              class="section-content"
              :class="{ expanded: expandedSections.memory }"
            >
              <div v-if="formData.memory_info" class="info-grid">
                <div class="info-item">
                  <label>{{ $t("bot.preset.memoryName") }}</label>
                  <span class="info-value">{{
                    formData.memory_info.memory_name
                  }}</span>
                </div>
                <div class="info-item">
                  <label>{{ $t("bot.preset.memoryType") }}</label>
                  <span class="info-value">{{
                    formData.memory_info.memory_type
                  }}</span>
                </div>
              </div>
              <div
                v-if="
                  formData.memory_info?.memory_params &&
                  Object.keys(formData.memory_info.memory_params).length
                "
                class="info-group"
              >
                <label>{{ $t("bot.preset.paramsConfig") }}</label>
                <pre class="info-value json-code">{{
                  formatJson(formData.memory_info.memory_params)
                }}</pre>
              </div>
              <div v-else class="info-empty">
                {{ $t("bot.preset.noMemoryConfig") }}
              </div>
            </div>
          </div>

          <!-- 5. 知识库配置 -->
          <div class="section-panel">
            <div class="section-header" @click="toggleSection('knowledgeBase')">
              <div class="section-title-wrapper">
                <h3 class="section-title">
                  {{ $t("bot.preset.knowledgeConfig") }}
                </h3>
              </div>
              <div class="section-header-actions">
                <span
                  class="section-badge"
                  v-if="formData.knowledge_bases_info?.length"
                >
                  {{ formData.knowledge_bases_info.length }}
                  {{ $t("bot.preset.units") }}
                </span>
                <span
                  class="collapse-icon"
                  :class="{ rotated: expandedSections.knowledgeBase }"
                >
                  ▶
                </span>
              </div>
            </div>
            <div
              class="section-content"
              :class="{ expanded: expandedSections.knowledgeBase }"
            >
              <div
                v-if="
                  formData.knowledge_bases_info &&
                  formData.knowledge_bases_info.length
                "
                class="knowledge-list"
              >
                <div
                  v-for="kb in formData.knowledge_bases_info"
                  :key="kb.kb_id"
                  class="knowledge-item"
                >
                  <div class="knowledge-header">
                    <span class="knowledge-name">{{ kb.kb_name }}</span>
                    <span class="knowledge-docs"
                      >{{ kb.document_count }}
                      {{ $t("bot.preset.documents") }}</span
                    >
                  </div>
                  <div v-if="kb.description" class="knowledge-desc">
                    {{ kb.description }}
                  </div>
                  <div class="knowledge-meta">
                    <span class="knowledge-embedding">{{
                      kb.embedding_model
                    }}</span>
                    <span class="knowledge-chunks"
                      >{{ kb.total_chunks }} {{ $t("bot.preset.chunks") }}</span
                    >
                  </div>
                </div>
              </div>
              <div v-else class="info-empty">
                {{ $t("bot.preset.noKnowledgeConfig") }}
              </div>
            </div>
          </div>

          <!-- 6. 插件配置 -->
          <div class="section-panel">
            <div class="section-header" @click="toggleSection('plugin')">
              <div class="section-title-wrapper">
                <h3 class="section-title">
                  {{ $t("bot.preset.pluginConfig") }}
                </h3>
              </div>
              <div class="section-header-actions">
                <span
                  class="section-badge"
                  v-if="formData.plugins_info?.length"
                >
                  {{ formData.plugins_info.length }}
                  {{ $t("bot.preset.units") }}
                </span>
                <span
                  class="collapse-icon"
                  :class="{ rotated: expandedSections.plugin }"
                >
                  ▶
                </span>
              </div>
            </div>
            <div
              class="section-content"
              :class="{ expanded: expandedSections.plugin }"
            >
              <div
                v-if="formData.plugins_info && formData.plugins_info.length"
                class="plugin-list"
              >
                <div
                  v-for="plugin in formData.plugins_info"
                  :key="plugin.plugin_id"
                  class="plugin-item"
                >
                  <div class="plugin-header">
                    <span class="plugin-name">{{ plugin.plugin_name }}</span>
                    <span class="plugin-class">{{ plugin.class_name }}</span>
                  </div>
                  <div v-if="plugin.module_path" class="plugin-path">
                    <span class="path-label"
                      >{{ $t("bot.preset.module") }}:</span
                    >
                    <code>{{ plugin.module_path }}</code>
                  </div>
                </div>
              </div>
              <div v-else class="info-empty">
                {{ $t("bot.preset.noPluginConfig") }}
              </div>
            </div>
          </div>

          <!-- 7. 高级配置 -->
          <div class="section-panel">
            <div class="section-header" @click="toggleSection('advanced')">
              <div class="section-title-wrapper">
                <h3 class="section-title">
                  {{ $t("bot.preset.advancedConfig") }}
                </h3>
              </div>
              <div class="section-header-actions">
                <span
                  class="collapse-icon"
                  :class="{ rotated: expandedSections.advanced }"
                >
                  ▶
                </span>
              </div>
            </div>
            <div
              class="section-content"
              :class="{ expanded: expandedSections.advanced }"
            >
              <div v-if="formData.overrides" class="info-group">
                <label>{{ $t("bot.preset.overrideConfig") }}</label>
                <pre class="info-value json-code">{{
                  formatJson(formData.overrides)
                }}</pre>
              </div>
              <div v-if="formData.channel_config" class="info-group">
                <label>{{ $t("bot.preset.channelConfig") }}</label>
                <pre class="info-value json-code">{{
                  formatJson(formData.channel_config)
                }}</pre>
              </div>
              <div
                v-if="!formData.overrides && !formData.channel_config"
                class="info-empty"
              >
                {{ $t("bot.preset.noAdvancedConfig") }}
              </div>
            </div>
          </div>

          <!-- 状态配置 -->
          <div class="section-panel">
            <div class="section-header">
              <div class="section-title-wrapper">
                <h3 class="section-title">{{ $t("bot.preset.status") }}</h3>
              </div>
              <div class="section-header-actions">
                <span class="collapse-icon">▶</span>
              </div>
            </div>
            <div class="section-content expanded">
              <div class="form-row">
                <div class="form-group checkbox-group">
                  <label class="checkbox-label">
                    <input v-model="formData.is_active" type="checkbox" />
                    {{ $t("bot.preset.isActive") }}
                  </label>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group checkbox-group">
                  <label class="checkbox-label">
                    <input v-model="formData.is_default" type="checkbox" />
                    {{ $t("bot.preset.isDefault") }}
                  </label>
                </div>
              </div>
            </div>
          </div>

          <!-- 错误提示 -->
          <div v-if="error" class="form-error">{{ error }}</div>

          <!-- 操作按钮 -->
          <div class="form-actions">
            <button
              type="button"
              class="btn btn-secondary"
              @click="handleClose"
            >
              {{ $t("common.cancel") }}
            </button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{
                saving
                  ? $t("bot.preset.saving")
                  : presetId
                    ? $t("common.save")
                    : $t("common.create")
              }}
            </button>
          </div>
        </form>
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
  padding: 20px;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.modal-title {
  font-size: 18px;
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
  transition: all 0.2s;
  color: var(--text-secondary);
}

.modal-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.loading-state,
.error-state {
  padding: 40px 24px;
  text-align: center;
  color: var(--text-secondary);
}

.error-state {
  color: #ef4444;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.preset-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-panel {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.section-panel:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: var(--primary-color);
}

.section-header {
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.2s;
}

.section-header:hover {
  background: var(--bg-hover);
}

.section-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-badge {
  font-size: 12px;
  padding: 2px 8px;
  background: var(--primary-color);
  color: white;
  border-radius: 10px;
}

.collapse-icon {
  font-size: 12px;
  color: var(--text-secondary);
  transition: transform 0.3s ease;
  cursor: pointer;
}

.collapse-icon.rotated {
  transform: rotate(90deg);
}

.section-content {
  padding: 0;
  max-height: 0;
  overflow: hidden;
  transition:
    max-height 0.3s ease-out,
    padding 0.3s ease;
  height: 0;
}

.section-content.expanded {
  max-height: 2000px;
  padding: 16px;
  height: auto;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: all 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.form-group input:disabled {
  background: var(--bg-disabled);
  color: var(--text-disabled);
  cursor: not-allowed;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-error {
  font-size: 12px;
  color: #ef4444;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.info-value {
  font-size: 14px;
  color: var(--text-primary);
  word-break: break-all;
}

.info-value.code {
  font-family: monospace;
  background: var(--bg-secondary);
  padding: 4px 8px;
  border-radius: 4px;
}

.info-value.system-prompt {
  font-style: italic;
  color: var(--text-secondary);
  line-height: 1.6;
}

.info-value.json-code {
  font-family: monospace;
  font-size: 12px;
  background: var(--bg-secondary);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  white-space: pre;
}

.info-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.info-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.info-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  margin: 2px;
  background: var(--primary-color);
  color: white;
  border-radius: 12px;
  font-size: 12px;
}

.knowledge-list,
.plugin-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.knowledge-item,
.plugin-item {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.knowledge-header,
.plugin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.knowledge-name,
.plugin-name {
  font-weight: 500;
  color: var(--text-primary);
}

.knowledge-docs,
.plugin-class {
  font-size: 12px;
  color: var(--text-secondary);
}

.knowledge-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.knowledge-meta,
.plugin-path {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
}

.path-label {
  color: var(--text-secondary);
}

code {
  font-family: monospace;
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: var(--bg-hover);
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 640px) {
  .modal-overlay {
    padding: 10px;
  }

  .modal-content {
    max-width: 100%;
    max-height: 95vh;
  }

  .modal-header {
    padding: 12px 16px;
  }

  .modal-title {
    font-size: 16px;
  }

  .modal-body {
    padding: 16px;
  }

  .section-content {
    padding: 12px;
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
