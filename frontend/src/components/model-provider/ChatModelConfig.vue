<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { t } from "../../locales";
import {
  getModelConfigs,
  createModelConfig,
  updateModelConfig,
  deleteModelConfig,
  getProviderModels,
} from "../../api/modelConfig";
import type { ModelConfigListItem } from "../../api/modelConfig";

const $t = t;

// 消息提示
const showMessage = ref(false);
const messageText = ref("");
const messageType = ref<"success" | "error" | "info">("info");
const messageTimer = ref<number | null>(null);

// 显示消息提示
const showToast = (
  text: string,
  type: "success" | "error" | "info" = "info",
) => {
  if (messageTimer.value) {
    clearTimeout(messageTimer.value);
  }
  messageText.value = text;
  messageType.value = type;
  showMessage.value = true;

  messageTimer.value = setTimeout(() => {
    showMessage.value = false;
  }, 3000);
};

// 确认对话框
const showConfirmDialog = ref(false);
const confirmText = ref("");
const confirmCallback = ref<(() => void) | null>(null);

// 显示确认对话框
const showConfirm = (text: string, callback: () => void) => {
  confirmText.value = text;
  confirmCallback.value = callback;
  showConfirmDialog.value = true;
};

// 确认操作
const handleConfirm = () => {
  if (confirmCallback.value) {
    confirmCallback.value();
  }
  showConfirmDialog.value = false;
  confirmCallback.value = null;
};

// 取消操作
const handleCancel = () => {
  showConfirmDialog.value = false;
  confirmCallback.value = null;
};

// 提供商数据
const providers = ref<
  {
    id: string;
    name: string;
    modelNames: string[];
    url: string;
    apiBase?: string;
    apiKey?: string;
    status: "active" | "inactive";
    disabledModels?: string[]; // 禁用的模型列表
  }[]
>([]);
const loading = ref(false);

// 选中的提供商
const selectedProvider = ref<{
  id: string;
  name: string;
  modelNames: string[];
  url: string;
  apiBase?: string;
  apiKey?: string;
  status: "active" | "inactive";
  disabledModels?: string[];
} | null>(null);

// 是否显示二级菜单
const showSubMenu = ref(false);
const subMenuRef = ref<HTMLElement | null>(null);
const addBtnRef = ref<HTMLElement | null>(null);

// 是否显示配置表单
const showConfigForm = ref(false);

// 当前正在配置的提供商
const configuringProvider = ref<{
  id: string;
  name: string;
  icon: string;
} | null>(null);

// 表单数据
const formData = ref({
  id: "",
  apiKey: "",
  apiBase: "",
});

// 是否显示 API Key
const showApiKey = ref(false);

// 是否显示模型列表弹窗
const showModelListModal = ref(false);
const availableModels = ref<
  Array<{ id: string; name: string; owned_by: string }>
>([]);
const fetchingModels = ref(false);

// 是否显示自定义模型弹窗
const showCustomModelModal = ref(false);
const customModelData = ref({
  modelId: "",
  modelName: "",
});

// 切换 API Key 显示/隐藏
const toggleApiKeyVisibility = () => {
  showApiKey.value = !showApiKey.value;
};

// 加载模型配置列表
const loadModelConfigs = async () => {
  loading.value = true;
  try {
    const response = await getModelConfigs("chat");
    if (response.data) {
      providers.value = response.data.map((item: ModelConfigListItem) => ({
        id: item.model_id,
        name: Array.isArray(item.model_name)
          ? item.model_name[0]
          : item.model_name,
        modelNames: item.model_name as string[],
        url: item.provider,
        apiBase: item.api_base,
        apiKey: item.api_key,
        status: item.is_active ? "active" : "inactive",
        disabledModels: item.disabled_models || [],
      }));
    }
  } catch (error) {
    console.error("加载模型配置失败:", error);
  } finally {
    loading.value = false;
  }
};

// 点击外部关闭二级菜单
const handleClickOutside = (event: MouseEvent) => {
  if (
    showSubMenu.value &&
    subMenuRef.value &&
    !subMenuRef.value.contains(event.target as Node) &&
    addBtnRef.value &&
    !addBtnRef.value.contains(event.target as Node)
  ) {
    showSubMenu.value = false;
  }
};

// 组件挂载时加载数据
onMounted(() => {
  loadModelConfigs();
  document.addEventListener("click", handleClickOutside);
});

// 组件卸载时移除事件监听和清理定时器
onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
  if (messageTimer.value) {
    clearTimeout(messageTimer.value);
  }
});

// 模型提供商列表
const availableProviders = ref([
  {
    id: "openai",
    name: "OpenAI",
    icon: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.896zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/></svg>`,
  },
  {
    id: "azure",
    name: "Azure OpenAI",
    icon: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5.483 21.3H24L14.025 4.013l-3.038 8.347 5.836 6.938L5.483 21.3zM13.23 2.7L6.105 8.677 0 19.253h5.505l7.735-10.034L13.23 2.7z"/></svg>`,
  },
  {
    id: "anthropic",
    name: "Anthropic",
    icon: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.304 3.541h-3.672l6.696 16.918h3.672zm-10.608 0L0 20.459h3.744l1.368-3.6h6.624l1.368 3.6h3.744L10.152 3.541zm-.264 10.656l1.944-5.184 1.944 5.184z"/></svg>`,
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    icon: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>`,
  },
  {
    id: "zhipu",
    name: "智谱 AI",
    icon: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`,
  },
  {
    id: "moonshot",
    name: "Moonshot",
    icon: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>`,
  },
  {
    id: "ollama",
    name: "Ollama",
    icon: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>`,
  },
  {
    id: "aliyun_bailian",
    name: "阿里云百炼",
    icon: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>`,
  },
]);

// 获取提供商图标
const getProviderIcon = (providerId: string) => {
  const provider = availableProviders.value.find((p) => p.id === providerId);
  return provider?.icon || availableProviders.value[0]?.icon || "";
};

// 选择提供商
const selectProvider = (provider: (typeof providers.value)[0]) => {
  selectedProvider.value = {
    ...provider,
    disabledModels: provider.disabledModels || [],
  };
  // 填充表单数据
  formData.value = {
    id: provider.id,
    apiKey: provider.apiKey || "",
    apiBase: provider.apiBase || "",
  };
  showConfigForm.value = false;
  configuringProvider.value = null;
  showSubMenu.value = false;
};

// 打开配置表单（直接显示，不要二级菜单）
const addProvider = () => {
  // 重置表单
  configuringProvider.value = null;
  formData.value = {
    id: "",
    apiKey: "",
    apiBase: "",
  };
  showConfigForm.value = true;
  selectedProvider.value = null;
};

// 选择模型提供商（点击即保存）
const selectModelProvider = async (
  provider: (typeof availableProviders.value)[0],
) => {
  // 检查是否已存在
  const exists = providers.value.some((p) => p.url === provider.id);
  if (exists) {
    showToast(`${provider.name} ${$t("provider.alreadyExists")}`, "error");
    return;
  }

  // 自动生成唯一 ID
  const modelId = `${provider.id}_${Date.now()}`;

  try {
    const configData = {
      model_id: modelId,
      model_name: [provider.name.toLowerCase()],
      model_type: "chat" as const,
      provider: provider.id,
      api_base: getDefaultApiBase(provider.id),
      api_key: "",
      is_active: true,
    };

    await createModelConfig(configData);
    await loadModelConfigs();

    // 关闭选择面板
    showConfigForm.value = false;

    // 显示成功提示
    showToast(`${provider.name} ${$t("provider.addSuccess")}`, "success");
  } catch (error: unknown) {
    console.error("添加配置失败:", error);
    showToast($t("provider.addFailed"), "error");
  }
};

// 获取默认 API Base
const getDefaultApiBase = (providerId: string) => {
  const defaults: Record<string, string> = {
    openai: "https://api.openai.com/v1",
    azure: "https://{your-resource}.openai.azure.com/",
    anthropic: "https://api.anthropic.com/v1",
    deepseek: "https://api.deepseek.com/v1",
    moonshot: "https://api.moonshot.cn/v1",
    zhipu: "https://open.bigmodel.cn/api/paas/v4",
    ollama: "http://localhost:11434",
    aliyun_bailian: "https://dashscope.aliyuncs.com/compatible-mode/v1",
  };
  return defaults[providerId] || "";
};

// 获取模型列表
const fetchModelList = async () => {
  if (!selectedProvider.value) {
    showToast("请先选择提供商", "error");
    return;
  }

  fetchingModels.value = true;
  try {
    const response = await getProviderModels(
      selectedProvider.value.url,
      selectedProvider.value.id,
    );

    if (response.data) {
      availableModels.value = response.data;
      showModelListModal.value = true;
      showToast(`获取到 ${response.data.length} 个模型`, "success");
    }
  } catch (error: any) {
    console.error("获取模型列表失败:", error);
    const errorMsg =
      error.response?.data?.detail || error.message || "获取失败";
    showToast(`获取模型列表失败：${errorMsg}`, "error");
  } finally {
    fetchingModels.value = false;
  }
};

// 从列表中选择模型添加
const selectModelFromList = async (model: { id: string; name: string }) => {
  if (!selectedProvider.value) return;

  // 检查是否已存在
  const exists = providers.value.some(
    (p) => p.modelNames.includes(model.id) || p.modelNames.includes(model.name),
  );

  if (exists) {
    showToast(`模型 ${model.name} 已存在`, "error");
    return;
  }

  try {
    // 获取提供商 ID（从 availableProviders 中查找）
    const providerInfo = availableProviders.value.find(
      (p) =>
        selectedProvider.value?.name.includes(p.name) ||
        selectedProvider.value?.url === p.id,
    );
    const providerId = providerInfo?.id || selectedProvider.value.url;

    // 查找该 provider 是否已有配置（相同 provider 和 api_base）
    let existingConfig = providers.value.find(
      (p) => p.url === providerId && p.apiBase === formData.value.apiBase,
    );

    if (existingConfig) {
      // 更新现有配置：添加新模型到 modelNames 数组
      const updatedModelNames = [...existingConfig.modelNames, model.name];

      await updateModelConfig(existingConfig.id, {
        model_name: updatedModelNames,
        disabled_models:
          existingConfig.disabled_models?.filter((m) => m !== model.name) || [],
      });

      await loadModelConfigs();

      // 选中更新后的配置，新模型默认启用
      const updatedConfig = providers.value.find(
        (p) => p.id === existingConfig.id,
      );
      if (updatedConfig) {
        // 确保新模型不在禁用列表中
        if (updatedConfig.disabledModels) {
          updatedConfig.disabledModels = updatedConfig.disabledModels.filter(
            (m) => m !== model.name,
          );
        }
        selectProvider(updatedConfig);
      }
    } else {
      // 创建新配置
      const configData = {
        model_id: `${providerId}_${Date.now()}`,
        model_name: [model.name],
        model_type: "chat" as const,
        provider: providerId,
        api_base: formData.value.apiBase,
        api_key: formData.value.apiKey,
        is_active: true,
        disabled_models: [], // 新配置没有禁用的模型
      };

      await createModelConfig(configData);
      await loadModelConfigs();

      // 选中新添加的配置
      const newModelConfig = providers.value.find((p) =>
        p.modelNames.includes(model.name),
      );
      if (newModelConfig) {
        newModelConfig.disabledModels = [];
        selectProvider(newModelConfig);
      }
    }

    showModelListModal.value = false;
    showToast(`已添加模型 ${model.name}`, "success");
  } catch (error: any) {
    console.error("添加模型失败:", error);
    showToast(`添加模型失败：${error.message}`, "error");
  }
};

// 打开自定义模型弹窗
const openCustomModelModal = () => {
  if (!selectedProvider.value) {
    showToast("请先选择提供商", "error");
    return;
  }

  customModelData.value = {
    modelId: "",
    modelName: "",
  };
  showCustomModelModal.value = true;
};

// 添加自定义模型
const addCustomModel = async () => {
  if (!selectedProvider.value) return;

  if (!customModelData.value.modelId || !customModelData.value.modelName) {
    showToast("请填写模型 ID 和名称", "error");
    return;
  }

  // 检查是否已存在
  const exists = providers.value.some(
    (p) =>
      p.modelNames.includes(customModelData.value.modelId) ||
      p.modelNames.includes(customModelData.value.modelName),
  );

  if (exists) {
    showToast(`模型 ${customModelData.value.modelName} 已存在`, "error");
    return;
  }

  try {
    // 获取提供商 ID（从 availableProviders 中查找）
    const providerInfo = availableProviders.value.find(
      (p) =>
        selectedProvider.value?.name.includes(p.name) ||
        selectedProvider.value?.url === p.id,
    );
    const providerId = providerInfo?.id || selectedProvider.value.url;

    // 查找该 provider 是否已有配置（相同 provider 和 api_base）
    let existingConfig = providers.value.find(
      (p) => p.url === providerId && p.apiBase === formData.value.apiBase,
    );

    // 清理 modelId，只保留小写字母、数字和下划线
    const cleanModelId = customModelData.value.modelId
      .toLowerCase()
      .replace(/[^a-z0-9_]/g, "_");

    if (existingConfig) {
      // 更新现有配置：添加新模型到 modelNames 数组
      const updatedModelNames = [
        ...existingConfig.modelNames,
        customModelData.value.modelName,
      ];

      await updateModelConfig(existingConfig.id, {
        model_name: updatedModelNames,
        disabled_models:
          existingConfig.disabled_models?.filter(
            (m) => m !== customModelData.value.modelName,
          ) || [],
      });

      await loadModelConfigs();

      // 选中更新后的配置，新模型默认启用
      const updatedConfig = providers.value.find(
        (p) => p.id === existingConfig.id,
      );
      if (updatedConfig) {
        // 确保新模型不在禁用列表中
        if (updatedConfig.disabledModels) {
          updatedConfig.disabledModels = updatedConfig.disabledModels.filter(
            (m) => m !== customModelData.value.modelName,
          );
        }
        selectProvider(updatedConfig);
      }
    } else {
      // 创建新配置
      const configData = {
        model_id: `${providerId}_${cleanModelId}`,
        model_name: [customModelData.value.modelName],
        model_type: "chat" as const,
        provider: providerId,
        api_base: formData.value.apiBase,
        api_key: formData.value.apiKey,
        is_active: true,
        disabled_models: [], // 新配置没有禁用的模型
      };

      await createModelConfig(configData);
      await loadModelConfigs();

      // 选中新添加的配置
      const newModelConfig = providers.value.find((p) =>
        p.modelNames.includes(customModelData.value.modelName),
      );
      if (newModelConfig) {
        newModelConfig.disabledModels = [];
        selectProvider(newModelConfig);
      }
    }

    showCustomModelModal.value = false;
    showToast(`已添加自定义模型 ${customModelData.value.modelName}`, "success");
  } catch (error: any) {
    console.error("添加自定义模型失败:", error);
    showToast(`添加自定义模型失败：${error.message}`, "error");
  }
};

// 保存配置（更新现有配置）
const saveConfig = async () => {
  if (!selectedProvider.value) {
    showToast($t("provider.selectProviderFirst"), "error");
    return;
  }

  try {
    // 将响应式 Proxy 转换为普通对象
    const disabledModelsArray = selectedProvider.value.disabledModels
      ? [...selectedProvider.value.disabledModels]
      : [];

    console.log("保存配置前的状态:", {
      id: selectedProvider.value.id,
      modelNames: [...selectedProvider.value.modelNames],
      disabledModels: disabledModelsArray,
    });

    const configData = {
      model_name: [...selectedProvider.value.modelNames],
      api_base: formData.value.apiBase,
      api_key: formData.value.apiKey,
      is_active: selectedProvider.value.status === "active",
      disabled_models: disabledModelsArray,
    };

    console.log("发送到后端的配置:", configData);

    await updateModelConfig(selectedProvider.value.id, configData);
    await loadModelConfigs();

    showConfigForm.value = false;

    // 显示成功提示
    showToast($t("provider.saveSuccess"), "success");
  } catch (error: unknown) {
    console.error("保存配置失败:", error);
    showToast($t("provider.saveFailed"), "error");
  }
};

// 取消配置
const cancelConfig = () => {
  showConfigForm.value = false;
  configuringProvider.value = null;
};

// 删除模型
const deleteModel = async (index: number) => {
  if (!selectedProvider.value) return;

  const modelName = selectedProvider.value.modelNames[index];

  showConfirm(`确定要删除模型 ${modelName} 吗？`, async () => {
    try {
      const updatedModelNames = selectedProvider.value.modelNames.filter(
        (_, i) => i !== index,
      );

      // 同时从 disabledModels 中移除
      if (selectedProvider.value.disabledModels) {
        selectedProvider.value.disabledModels =
          selectedProvider.value.disabledModels.filter((m) => m !== modelName);
      }

      if (updatedModelNames.length === 0) {
        // 如果删除后没有模型了，删除整个配置
        await deleteModelConfig(selectedProvider.value.id);
        showToast(`已删除模型 ${modelName}`, "success");
      } else {
        // 更新配置，移除该模型
        await updateModelConfig(selectedProvider.value.id, {
          model_name: updatedModelNames,
          disabled_models: selectedProvider.value.disabledModels,
        });
        showToast(`已删除模型 ${modelName}`, "success");
      }

      await loadModelConfigs();

      // 如果当前选中的配置被删除了，选中第一个配置
      if (updatedModelNames.length === 0 && providers.value.length > 0) {
        selectProvider(providers.value[0]);
      } else if (updatedModelNames.length > 0) {
        // 更新当前选中的配置
        const updatedConfig = providers.value.find(
          (p) => p.id === selectedProvider.value?.id,
        );
        if (updatedConfig) {
          selectProvider(updatedConfig);
        }
      }
    } catch (error: any) {
      console.error("删除模型失败:", error);
      showToast(`删除失败：${error.message}`, "error");
    }
  });
};

// 切换模型状态
const toggleModelStatus = async (index: number, event: Event) => {
  if (!selectedProvider.value) return;

  const target = event.target as HTMLInputElement;
  const isActive = target.checked;
  const modelName = selectedProvider.value.modelNames[index];

  try {
    // 更新本地状态
    if (!selectedProvider.value.disabledModels) {
      selectedProvider.value.disabledModels = [];
    }

    if (isActive) {
      // 启用：从禁用列表中移除
      selectedProvider.value.disabledModels =
        selectedProvider.value.disabledModels.filter((m) => m !== modelName);
    } else {
      // 禁用：添加到禁用列表
      if (!selectedProvider.value.disabledModels.includes(modelName)) {
        selectedProvider.value.disabledModels.push(modelName);
      }
    }

    // 同步更新到 providers 列表
    const providerInList = providers.value.find(
      (p) => p.id === selectedProvider.value?.id,
    );
    if (providerInList) {
      if (!providerInList.disabledModels) {
        providerInList.disabledModels = [];
      }
      if (isActive) {
        providerInList.disabledModels = providerInList.disabledModels.filter(
          (m) => m !== modelName,
        );
      } else {
        if (!providerInList.disabledModels.includes(modelName)) {
          providerInList.disabledModels.push(modelName);
        }
      }
    }

    console.log(`模型 ${modelName} 状态切换为：${isActive ? "启用" : "禁用"}`);
    if (isActive) {
      showToast(`模型 ${modelName} 已启用`, "success");
    } else {
      showToast(`模型 ${modelName} 已禁用`, "info");
    }
  } catch (error: any) {
    console.error("切换模型状态失败:", error);
    target.checked = !isActive; // 恢复状态
    showToast(`切换失败：${error.message}`, "error");
  }
};

// 删除提供商
const deleteProvider = async (providerId: string) => {
  // 显示二次确认
  showConfirm($t("provider.deleteConfirm"), async () => {
    try {
      await deleteModelConfig(providerId);
      await loadModelConfigs();
      if (selectedProvider.value?.id === providerId) {
        selectedProvider.value = null;
      }
      // 显示成功提示
      showToast($t("provider.deleteSuccess"), "success");
    } catch (error: unknown) {
      console.error("删除配置失败:", error);
      showToast($t("provider.deleteFailed"), "error");
    }
  });
};
</script>

<template>
  <div class="chat-model-config">
    <!-- 左侧提供商列表 -->
    <div class="provider-list-section">
      <div class="section-header">
        <h3 class="section-title">
          {{ $t("provider.providers") || "提供商源" }}
        </h3>
        <div class="add-btn-wrapper">
          <button ref="addBtnRef" class="add-btn" @click="addProvider">
            <svg class="add-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
            </svg>
            <span>{{ $t("provider.add") || "新增" }}</span>
          </button>
        </div>
      </div>

      <!-- 新增提供商选择面板 -->
      <div
        v-if="showConfigForm && !configuringProvider"
        class="add-provider-panel"
      >
        <div class="panel-header">
          <h4>{{ $t("provider.selectModelProvider") }}</h4>
          <button class="panel-close" @click="showConfigForm = false">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
              />
            </svg>
          </button>
        </div>
        <div class="provider-grid">
          <div
            v-for="provider in availableProviders"
            :key="provider.id"
            class="provider-card"
            @click="selectModelProvider(provider)"
          >
            <div class="provider-card-icon" v-html="provider.icon"></div>
            <div class="provider-card-name">{{ provider.name }}</div>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <svg class="loading-icon" viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"
          />
        </svg>
        <span>{{ $t("provider.loading") }}</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="providers.length === 0" class="empty-list-state">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"
          />
        </svg>
        <span>{{ $t("provider.noProviders") }}</span>
      </div>

      <div v-else class="provider-list">
        <div
          v-for="provider in providers"
          :key="provider.id"
          class="provider-item"
          :class="{ active: selectedProvider?.id === provider.id }"
          @click="selectProvider(provider)"
        >
          <div
            class="provider-icon"
            v-html="getProviderIcon(provider.url)"
          ></div>
          <div class="provider-info">
            <div class="provider-name">{{ provider.id }}</div>
            <div class="provider-url">{{ provider.apiBase }}</div>
          </div>
          <div class="provider-actions">
            <div
              v-if="provider.status === 'active'"
              class="status-dot active"
            ></div>
            <button
              class="delete-btn"
              @click.stop="deleteProvider(provider.id)"
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path
                  d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧详情区域 -->
    <div class="provider-detail">
      <!-- 空状态 -->
      <div v-if="!selectedProvider && !showConfigForm" class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"
          />
        </svg>
        <p class="empty-text">
          {{ $t("provider.selectProvider") || "请选择一个提供商源" }}
        </p>
      </div>

      <!-- 配置表单（选中提供商后直接显示） -->
      <div v-else-if="selectedProvider" class="config-form">
        <div class="form-header">
          <div class="header-left">
            <h2>{{ selectedProvider.name }}</h2>
            <p class="provider-url-display">{{ selectedProvider.url }}</p>
          </div>
          <button class="save-btn" @click="saveConfig">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
            </svg>
            <span>{{ $t("provider.saveConfig") }}</span>
          </button>
        </div>

        <div class="form-body">
          <div class="form-item">
            <label>{{ $t("provider.id") }}</label>
            <div class="form-input-wrapper">
              <input
                v-model="formData.id"
                type="text"
                class="form-input"
                :placeholder="$t('provider.id')"
              />
            </div>
          </div>

          <div class="form-item">
            <label>
              <div>{{ $t("provider.apiKey") }}</div>
              <div class="form-hint">{{ $t("provider.apiKeyHint") }}</div>
            </label>
            <div class="form-input-wrapper">
              <input
                v-model="formData.apiKey"
                :type="showApiKey ? 'text' : 'password'"
                class="form-input"
                :placeholder="$t('provider.apiKeyHint')"
              />
              <button class="input-action-btn" @click="toggleApiKeyVisibility">
                <svg
                  v-if="!showApiKey"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  width="16"
                  height="16"
                >
                  <path
                    d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"
                  />
                </svg>
                <svg
                  v-else
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  width="16"
                  height="16"
                >
                  <path
                    d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"
                  />
                </svg>
              </button>
              <button class="input-action-btn">
                {{ $t("provider.addMore") }}
              </button>
            </div>
          </div>

          <div class="form-item">
            <label>
              <div>{{ $t("provider.apiBase") }}</div>
              <div class="form-hint">{{ $t("provider.apiBaseHint") }}</div>
            </label>
            <div class="form-input-wrapper">
              <input
                v-model="formData.apiBase"
                type="text"
                class="form-input"
                :placeholder="$t('provider.apiBaseHint')"
              />
            </div>
          </div>

          <div class="form-item">
            <div class="form-label-with-action">
              <label>{{ $t("provider.advancedConfig") }}</label>
              <svg class="expand-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" />
              </svg>
            </div>
          </div>

          <!-- 已配置的模型列表 -->
          <div class="models-section">
            <div class="models-header">
              <div class="models-title-section">
                <h3>{{ $t("provider.configuredModels") }}</h3>
                <div class="search-box">
                  <svg
                    class="search-icon"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path
                      d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"
                    />
                  </svg>
                  <input
                    type="text"
                    class="search-input"
                    :placeholder="$t('provider.searchModels')"
                  />
                </div>
              </div>
              <div class="models-actions">
                <button class="action-btn" @click="fetchModelList">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path
                      d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"
                    />
                  </svg>
                  <span>{{ $t("provider.getModelList") }}</span>
                </button>
                <button
                  class="action-btn primary"
                  @click="openCustomModelModal"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
                  </svg>
                  <span>{{ $t("provider.customModel") }}</span>
                </button>
              </div>
            </div>

            <div class="models-list">
              <div
                v-for="(model, index) in selectedProvider.modelNames"
                :key="model"
                class="model-item"
              >
                <div class="model-info">
                  <div class="model-name">{{ model }}</div>
                  <div class="model-id">
                    {{ model.split("/").pop() || model }}
                  </div>
                </div>
                <div class="model-actions">
                  <label class="switch">
                    <input
                      type="checkbox"
                      :checked="
                        !selectedProvider.disabledModels?.includes(model)
                      "
                      @change="toggleModelStatus(index, $event)"
                    />
                    <span class="slider"></span>
                  </label>
                  <button
                    class="icon-btn delete"
                    :title="$t('provider.delete')"
                    @click="deleteModel(index)"
                  >
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path
                        d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="showMessage" class="toast-message" :class="messageType">
      <svg
        v-if="messageType === 'success'"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
      </svg>
      <svg
        v-else-if="messageType === 'error'"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path
          d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"
        />
      </svg>
      <span>{{ messageText }}</span>
    </div>

    <!-- 确认对话框 -->
    <div v-if="showConfirmDialog" class="confirm-overlay">
      <div class="confirm-dialog">
        <div class="confirm-header">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"
            />
          </svg>
          <span>{{ $t("provider.confirmTitle") }}</span>
        </div>
        <div class="confirm-content">
          {{ confirmText }}
        </div>
        <div class="confirm-actions">
          <button class="confirm-cancel" @click="handleCancel">
            {{ $t("provider.confirmCancel") }}
          </button>
          <button class="confirm-ok" @click="handleConfirm">
            {{ $t("provider.confirmOk") }}
          </button>
        </div>
      </div>
    </div>

    <!-- 模型列表弹窗 -->
    <div
      v-if="showModelListModal"
      class="modal-overlay"
      @click.self="showModelListModal = false"
    >
      <div class="modal-dialog">
        <div class="modal-header">
          <h3>选择模型</h3>
          <button class="modal-close" @click="showModelListModal = false">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
              />
            </svg>
          </button>
        </div>
        <div class="modal-content">
          <div v-if="fetchingModels" class="loading-state">
            <svg class="loading-icon" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"
              />
            </svg>
            <span>正在获取模型列表...</span>
          </div>
          <div v-else-if="availableModels.length === 0" class="empty-state">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"
              />
            </svg>
            <span>暂无可用模型</span>
          </div>
          <div v-else class="model-list">
            <div
              v-for="model in availableModels"
              :key="model.id"
              class="model-item"
              @click="selectModelFromList(model)"
            >
              <div class="model-item-info">
                <div class="model-item-name">{{ model.name }}</div>
                <div class="model-item-id">{{ model.id }}</div>
              </div>
              <svg class="add-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 自定义模型弹窗 -->
    <div
      v-if="showCustomModelModal"
      class="modal-overlay"
      @click.self="showCustomModelModal = false"
    >
      <div class="modal-dialog">
        <div class="modal-header">
          <h3>添加自定义模型</h3>
          <button class="modal-close" @click="showCustomModelModal = false">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
              />
            </svg>
          </button>
        </div>
        <div class="modal-content">
          <div class="form-item">
            <label>模型 ID</label>
            <input
              v-model="customModelData.modelId"
              type="text"
              class="form-input"
              placeholder="例如：gpt-4-turbo"
            />
          </div>
          <div class="form-item">
            <label>模型名称</label>
            <input
              v-model="customModelData.modelName"
              type="text"
              class="form-input"
              placeholder="例如：GPT-4 Turbo"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showCustomModelModal = false">
            {{ $t("provider.confirmCancel") }}
          </button>
          <button class="btn-primary" @click="addCustomModel">添加模型</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-model-config {
  display: flex;
  gap: 24px;
  height: 100%;
}

/* 左侧提供商列表 */
.provider-list-section {
  width: 320px;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 16px;
  position: relative;
}

/* 浅色模式下使用纯白色背景 */
:root:not(.dark) .provider-list-section {
  background: #ffffff;
}

/* 新增提供商选择面板 */
.add-provider-panel {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 16px;
  z-index: 10;
  animation: fadeIn 0.2s ease;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.panel-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.panel-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.panel-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.panel-close svg {
  width: 20px;
  height: 20px;
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
  overflow-y: auto;
  max-height: calc(100% - 60px);
  padding: 4px;
}

.provider-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.provider-card:hover {
  background: var(--bg-hover);
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.provider-card-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
}

.provider-card-icon svg {
  width: 100%;
  height: 100%;
}

.provider-card-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  text-align: center;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.add-btn-wrapper {
  position: relative;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-btn:hover {
  opacity: 0.9;
}

.add-btn svg {
  width: 16px;
  height: 16px;
  fill: white;
}

/* 二级菜单 */
.sub-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  z-index: 100;
}

.sub-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sub-menu-item:hover {
  background: var(--bg-hover);
}

.sub-menu-item:first-child {
  border-radius: 8px 8px 0 0;
}

.sub-menu-item:last-child {
  border-radius: 0 0 8px 8px;
}

.provider-icon-svg {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.provider-icon-svg svg {
  width: 100%;
  height: 100%;
}

.provider-name-text {
  font-size: 14px;
  color: var(--text-primary);
}

/* 加载状态 */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: var(--text-secondary);
  font-size: 14px;
}

.loading-icon {
  width: 20px;
  height: 20px;
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

/* 空状态 */
.empty-list-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 24px;
  color: var(--text-tertiary);
  text-align: center;
}

.empty-list-state svg {
  width: 40px;
  height: 40px;
  opacity: 0.5;
}

.empty-list-state span {
  font-size: 13px;
}

.provider-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
}

.provider-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.provider-item:hover {
  background: var(--bg-hover);
}

.provider-item.active {
  background: var(--primary-light);
  border-color: var(--primary-color);
}

.provider-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.provider-icon svg {
  width: 20px;
  height: 20px;
}

.provider-info {
  flex: 1;
  min-width: 0;
}

.provider-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 2px;
}

:root.dark .provider-name {
  color: #ffffff;
}

.provider-url {
  font-size: 12px;
  color: #6a6a6a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:root.dark .provider-url {
  color: #b0b0b0;
}

.provider-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-tertiary);
}

.status-dot.active {
  background: #22c55e;
}

.delete-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.delete-btn:hover {
  background: var(--bg-hover);
  color: #ef4444;
}

.delete-btn svg {
  width: 16px;
  height: 16px;
}

/* 右侧详情区域 */
.provider-detail {
  flex: 1;
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 24px;
  overflow-y: auto;
}

/* 浅色模式下使用纯白色背景 */
:root:not(.dark) .provider-detail {
  background: #ffffff;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
}

.detail-content h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.detail-content p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 8px 0;
}

/* 配置表单 */
.config-form {
  height: 100%;
}

/* 浅色模式下使用纯白色背景 */
:root:not(.dark) .config-form {
  background: #ffffff;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  flex: 1;
}

.form-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.provider-url-display {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.save-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #22c55e;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.save-btn:hover {
  opacity: 0.9;
}

.save-btn svg {
  width: 18px;
  height: 18px;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.form-item > label {
  width: 200px;
  padding-top: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  flex-shrink: 0;
}

:root.dark .form-item > label {
  color: #ffffff;
}

.form-label-with-action {
  width: 200px;
  padding-top: 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.form-label-with-action label {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  cursor: pointer;
}

:root.dark .form-label-with-action label {
  color: #ffffff;
}

.expand-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

.form-input-wrapper {
  flex: 1;
  display: flex;
  gap: 8px;
}

.form-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.9);
  color: #1a1a1a;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
}

.form-input:focus {
  border-color: var(--primary-color);
  background: rgba(255, 255, 255, 0.95);
}

.form-input::placeholder {
  color: #6a6a6a;
}

.input-action-btn {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: #1a1a1a;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.input-action-btn:hover {
  background: rgba(255, 255, 255, 0.95);
}

.form-hint {
  width: 200px;
  flex-shrink: 0;
  font-size: 12px;
  color: #6a6a6a;
}

:root.dark .form-hint {
  color: #b0b0b0;
}

/* 模型列表样式 */
.models-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.models-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.models-title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.models-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

:root.dark .models-header h3 {
  color: #ffffff;
}

.models-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.search-box {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
  pointer-events: none;
}

.search-input {
  width: 240px;
  padding: 8px 12px 8px 32px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: #1a1a1a;
  background: rgb(245, 247, 250);
}

:root.dark .search-input {
  background: rgb(50, 50, 50);
  color: #ffffff;
}

.search-input::placeholder {
  color: #6a6a6a;
}

:root.dark .search-input::placeholder {
  color: #b0b0b0;
}

.search-input:focus {
  outline: none;
  background: rgb(240, 242, 245);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: rgb(236, 245, 255);
  color: #1a1a1a;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

:root.dark .action-btn {
  color: #ffffff;
  background: rgb(50, 50, 50);
}

.action-btn:hover {
  background: rgb(219, 234, 254);
}

.action-btn.primary {
  background: rgb(236, 245, 255);
  color: #1a1a1a;
}

:root.dark .action-btn.primary {
  color: #ffffff;
  background: rgb(50, 50, 50);
}

.action-btn.primary:hover {
  background: rgb(219, 234, 254);
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

:root.dark .action-btn svg {
  fill: #ffffff;
}

.models-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: white;
  border: 1px solid rgb(219, 234, 254);
  border-radius: 12px;
  padding: 8px;
}

.model-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  border: none;
}

.model-item:hover {
  background: rgba(255, 255, 255, 0.95);
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.model-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}

.model-id {
  font-size: 12px;
  color: #6a6a6a;
}

.model-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 36px;
  height: 20px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgb(186, 212, 235);
  transition: 0.3s;
  border-radius: 20px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: rgb(147, 197, 238);
}

input:checked + .slider:before {
  transform: translateX(16px);
}

/* 图标按钮 */
.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.icon-btn.delete:hover {
  background: rgba(220, 38, 38, 0.1);
  color: rgb(220, 38, 38);
}

.icon-btn svg {
  width: 16px;
  height: 16px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.cancel-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* 消息提示 */
.toast-message {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  animation: slideDown 0.3s ease;
}

.toast-message.success {
  background: rgb(220, 252, 231);
  color: rgb(22, 163, 74);
  border: 1px solid rgb(134, 239, 172);
}

.toast-message.error {
  background: rgb(254, 226, 226);
  color: rgb(220, 38, 38);
  border: 1px solid rgb(252, 165, 165);
}

.toast-message.info {
  background: rgb(236, 245, 255);
  color: rgb(37, 99, 235);
  border: 1px solid rgb(147, 197, 253);
}

.toast-message svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

/* 确认对话框 */
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: fadeIn 0.2s ease;
}

.confirm-dialog {
  background: white;
  border-radius: 12px;
  padding: 24px;
  min-width: 400px;
  max-width: 500px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  animation: scaleIn 0.2s ease;
}

:root.dark .confirm-dialog {
  background: rgb(30, 30, 30);
}

.confirm-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.confirm-header svg {
  width: 24px;
  height: 24px;
  color: rgb(234, 179, 8);
  flex-shrink: 0;
}

.confirm-header span {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

:root.dark .confirm-header span {
  color: #ffffff;
}

.confirm-content {
  font-size: 15px;
  color: #4a4a4a;
  line-height: 1.6;
  margin-bottom: 24px;
}

:root.dark .confirm-content {
  color: #b0b0b0;
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.confirm-cancel {
  padding: 8px 20px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.confirm-cancel:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.confirm-ok {
  padding: 8px 20px;
  background: rgb(220, 38, 38);
  border: none;
  border-radius: 6px;
  font-size: 14px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.confirm-ok:hover {
  background: rgb(185, 28, 28);
}

/* 动画 */
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translate(-50%, -20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 弹窗样式 */
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
  animation: fadeIn 0.2s ease;
}

.modal-dialog {
  background: var(--bg-primary);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  animation: scaleIn 0.2s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.modal-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.modal-close svg {
  width: 18px;
  height: 18px;
}

.modal-content {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.btn-cancel {
  padding: 8px 20px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-primary {
  padding: 8px 20px;
  background: var(--primary-color);
  border: none;
  border-radius: 6px;
  font-size: 14px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  opacity: 0.9;
}

/* 模型列表 */
.model-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.model-item:hover {
  background: var(--bg-hover);
  transform: translateX(4px);
}

.model-item-info {
  flex: 1;
}

.model-item-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.model-item-id {
  font-size: 12px;
  color: var(--text-secondary);
}

.add-icon {
  width: 20px;
  height: 20px;
  color: var(--primary-color);
  flex-shrink: 0;
}

/* 表单输入框 */
.modal-content .form-item {
  margin-bottom: 16px;
}

.modal-content .form-item label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.modal-content .form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: all 0.2s;
}

.modal-content .form-input:focus {
  border-color: var(--primary-color);
  background: var(--bg-primary);
}
</style>
