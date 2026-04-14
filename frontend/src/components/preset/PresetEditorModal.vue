<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { ElMessage } from "element-plus";
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
// 扁平化的模型列表（只包含启用的）
const flatModels = ref<
  { model_name: string; provider: string; is_active: boolean }[]
>([]);
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
  status: false,
});

// 加载模型提供商列表
const loadModelConfigs = async () => {
  try {
    const response = await getModelConfigs("chat");
    modelConfigs.value = response.data || [];

    // 将所有模型扁平化为一个列表（只包含启用的且未被禁用的模型）
    flatModels.value = [];
    for (const config of modelConfigs.value) {
      if (config.is_active) {
        // 只添加启用的模型配置
        for (const model_name of config.model_name) {
          // 检查模型是否被禁用
          const isDisabled =
            config.disabled_models &&
            config.disabled_models.includes(model_name);
          if (!isDisabled) {
            flatModels.value.push({
              model_name: model_name,
              provider: config.provider,
              is_active: config.is_active,
            });
          }
        }
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

// 提示词切换时立即更新详情
const onPromptChange = () => {
  const selectedPromptId = formData.value.selected_prompt;
  if (selectedPromptId) {
    const prompt = promptConfigs.value.find(
      (p) => p.prompt_id === selectedPromptId,
    );
    if (prompt) {
      formData.value.prompt_info = {
        prompt_id: prompt.prompt_id,
        prompt_name: prompt.prompt_name,
        system_prompt: prompt.system_prompt,
        variables: prompt.variables || [],
        temperature_override: prompt.temperature_override,
      };
    }
  } else {
    formData.value.prompt_info = undefined;
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

    // 显示保存成功提示
    ElMessage.success(props.presetId ? "修改成功" : "创建成功");

    emit("success");
  } catch (err: any) {
    error.value = props.presetId
      ? $t("bot.preset.updateFailed")
      : $t("bot.preset.createFailed");
    console.error(props.presetId ? "更新预设失败:" : "创建预设失败:", err);

    // 显示错误提示
    ElMessage.error(err.message || (props.presetId ? "修改失败" : "创建失败"));
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
                      :disabled="!model.is_active"
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
                    @change="onPromptChange"
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

          <!-- 状态配置（整合到高级配置中） -->
          <div class="section-panel" v-if="!presetId">
            <div class="section-header" @click="toggleSection('status')">
              <div class="section-title-wrapper">
                <h3 class="section-title">
                  {{ $t("bot.preset.statusConfig") || "状态配置" }}
                </h3>
              </div>
              <div class="section-header-actions">
                <span
                  class="collapse-icon"
                  :class="{ rotated: expandedSections.status }"
                >
                  ▶
                </span>
              </div>
            </div>
            <div
              class="section-content"
              :class="{ expanded: expandedSections.status }"
            >
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
        </form>
      </div>

      <!-- 保存按钮（固定在右下角） -->
      <button
        type="button"
        class="save-btn"
        :disabled="saving"
        @click="savePreset"
        :title="
          saving
            ? $t('bot.preset.saving')
            : presetId
              ? $t('common.save')
              : $t('common.create')
        "
      >
        <svg
          v-if="!saving"
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path
            d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"
          ></path>
          <polyline points="17 21 17 13 7 13 7 21"></polyline>
          <polyline points="7 3 7 8 15 8"></polyline>
        </svg>
        <svg
          v-else
          class="spinner"
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <line x1="12" y1="2" x2="12" y2="6"></line>
          <line x1="12" y1="18" x2="12" y2="22"></line>
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
          <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
          <line x1="2" y1="12" x2="6" y2="12"></line>
          <line x1="18" y1="12" x2="22" y2="12"></line>
          <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
          <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
        </svg>
      </button>
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
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 24px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: var(--bg-primary);
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(99, 102, 241, 0.1);
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.3s ease-out;
  position: relative;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  padding: 20px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.modal-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--text-secondary);
}

.modal-close:hover {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  transform: rotate(90deg);
}

.loading-state,
.error-state {
  padding: 60px 24px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
}

.error-state {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
  border-radius: 8px;
  margin: 24px;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  padding-bottom: 80px;
  background: var(--bg-primary);
}

.modal-body::-webkit-scrollbar {
  width: 8px;
}

.modal-body::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
  transition: background 0.2s;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: var(--primary-color);
}

.preset-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-panel {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  background: var(--bg-primary);
}

.section-header {
  padding: 16px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.section-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 4px 10px;
  background: var(--primary-color);
  color: white;
  border-radius: 12px;
}

.collapse-icon {
  font-size: 12px;
  color: var(--text-secondary);
}

.collapse-icon.rotated {
  transform: rotate(90deg);
}

.section-content {
  padding: 0;
  max-height: 0;
  overflow: hidden;
  height: 0;
  background: var(--bg-primary);
}

.section-content.expanded {
  max-height: 2000px;
  padding: 20px;
  height: auto;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.form-group label::before {
  content: "";
  width: 3px;
  height: 12px;
  background: var(--primary-color);
  border-radius: 2px;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group input:disabled {
  background: var(--bg-disabled);
  color: var(--text-disabled);
  cursor: not-allowed;
  opacity: 0.7;
}

.form-group textarea {
  resize: vertical;
  min-height: 100px;
  line-height: 1.6;
}

.form-error {
  font-size: 12px;
  color: #ef4444;
  font-weight: 500;
  padding-left: 6px;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-4px);
  }
  75% {
    transform: translateX(4px);
  }
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
  transition: color 0.2s;
}

.checkbox-label:hover {
  color: #6366f1;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #6366f1;
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
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 14px;
  color: var(--text-primary);
  word-break: break-all;
}

.info-value.code {
  background: var(--bg-secondary);
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.info-value.system-prompt {
  color: var(--text-secondary);
  line-height: 1.6;
}

.info-value.json-code {
  font-family: "Fira Code", monospace;
  font-size: 12px;
  background: var(--bg-secondary);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  white-space: pre;
  border: 1px solid var(--border-color);
}

.info-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.info-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.info-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  margin: 2px;
  background: var(--primary-color);
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.knowledge-list,
.plugin-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.knowledge-item,
.plugin-item {
  padding: 14px;
  background: var(--bg-secondary);
  border-radius: 8px;
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
  font-weight: 700;
  color: var(--text-primary);
  font-size: 14px;
}

.knowledge-docs,
.plugin-class {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: "Fira Code", monospace;
}

.knowledge-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.6;
}

.knowledge-meta,
.plugin-path {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
  font-family: "Fira Code", monospace;
}

.path-label {
  color: var(--text-secondary);
}

code {
  background: var(--bg-secondary);
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid var(--border-color);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
}

/* 保存按钮（固定在右下角） */
.save-btn {
  position: absolute;
  bottom: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--primary-color);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 10;
  transition: transform 0.1s ease;
}

.save-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.save-btn .spinner {
  animation: spin 1s linear infinite;
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: grayscale(100%);
}

/* 响应式 */
@media (max-width: 640px) {
  .modal-overlay {
    padding: 12px;
  }

  .modal-content {
    max-width: 100%;
    max-height: 95vh;
  }

  .modal-header {
    padding: 16px;
  }

  .modal-title {
    font-size: 18px;
  }

  .modal-body {
    padding: 16px;
  }

  .section-content {
    padding: 16px;
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
