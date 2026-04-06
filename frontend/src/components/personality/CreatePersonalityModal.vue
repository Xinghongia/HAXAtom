<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { t } from "../../locales";
import type {
  CreatePromptConfigRequest,
  UpdatePromptConfigRequest,
  PresetDialogue,
  PromptConfig,
} from "../../api/promptConfig";

const props = defineProps<{
  modelValue: boolean;
  isEdit?: boolean;
  editData?: PromptConfig | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "submit", data: CreatePromptConfigRequest): void;
  (e: "update", data: UpdatePromptConfigRequest): void;
}>();

// 计算属性替代 visible
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

const $t = computed(() => t);

// 表单数据
const formData = ref<CreatePromptConfigRequest>({
  prompt_name: "",
  description: "",
  system_prompt: "",
  variables: [],
  temperature_override: undefined,
  is_active: true,
  selected_tools: [],
  use_all_tools: true,
  preset_dialogues: [],
});

// 展开状态
const expandedSections = ref({
  tools: true,
  skills: true,
  dialogues: true,
});

// 工具选择模式
const toolSelectionMode = ref<"all" | "custom">("all");

// 预设对话列表
const dialogues = ref<PresetDialogue[]>([]);

// 弹窗标题
const modalTitle = computed(() => {
  return props.isEdit
    ? $t.value("personality.editTitle") || "编辑人格"
    : $t.value("personality.createTitle") || "创建新人格";
});

// 监听编辑数据变化
watch(
  () => props.editData,
  (newData) => {
    if (newData && props.isEdit) {
      formData.value = {
        prompt_name: newData.prompt_name,
        description: newData.description || "",
        system_prompt: newData.system_prompt,
        variables: newData.variables || [],
        temperature_override: newData.temperature_override,
        is_active: newData.is_active,
        selected_tools: newData.selected_tools || [],
        use_all_tools: newData.use_all_tools,
        preset_dialogues: newData.preset_dialogues || [],
      };
      dialogues.value = newData.preset_dialogues
        ? [...newData.preset_dialogues]
        : [];
      toolSelectionMode.value = newData.use_all_tools ? "all" : "custom";
    }
  },
  { immediate: true },
);

// 切换展开状态
const toggleSection = (section: "tools" | "skills" | "dialogues") => {
  expandedSections.value[section] = !expandedSections.value[section];
};

// 添加对话对
const addDialoguePair = () => {
  dialogues.value.push({ role: "user", content: "" });
  dialogues.value.push({ role: "assistant", content: "" });
};

// 删除对话
const removeDialogue = (index: number) => {
  dialogues.value.splice(index, 1);
};

// 关闭弹窗
const closeModal = () => {
  visible.value = false;
  if (!props.isEdit) {
    resetForm();
  }
};

// 重置表单
const resetForm = () => {
  formData.value = {
    prompt_name: "",
    description: "",
    system_prompt: "",
    variables: [],
    temperature_override: undefined,
    is_active: true,
    selected_tools: [],
    use_all_tools: true,
    preset_dialogues: [],
  };
  dialogues.value = [];
  toolSelectionMode.value = "all";
};

// 提交表单
const handleSubmit = () => {
  // 过滤掉空内容的对话
  formData.value.preset_dialogues = dialogues.value.filter(
    (d) => d.content.trim() !== "",
  );
  formData.value.use_all_tools = toolSelectionMode.value === "all";

  if (props.isEdit) {
    // 编辑模式：只发送有变化的字段
    const updateData: UpdatePromptConfigRequest = {
      prompt_name: formData.value.prompt_name,
      description: formData.value.description,
      system_prompt: formData.value.system_prompt,
      variables: formData.value.variables,
      temperature_override: formData.value.temperature_override,
      is_active: formData.value.is_active,
      selected_tools: formData.value.selected_tools,
      use_all_tools: formData.value.use_all_tools,
      preset_dialogues: formData.value.preset_dialogues,
    };
    emit("update", updateData);
  } else {
    // 创建模式
    emit("submit", { ...formData.value });
  }
  closeModal();
};
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <!-- 头部 -->
        <div class="modal-header">
          <h2 class="modal-title">
            {{ modalTitle }}
          </h2>
          <button class="modal-close" @click="closeModal">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
              />
            </svg>
          </button>
        </div>

        <!-- 内容区 -->
        <div class="modal-body">
          <!-- 文件夹提示 -->
          <div class="folder-hint">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"
              />
            </svg>
            <span
              >{{ $t("personality.createInFolder") || "将在" }} 「{{
                $t("personality.allPersonalities") || "全部人格"
              }}」{{ $t("personality.createInFolderSuffix") || "中创建" }}</span
            >
          </div>

          <div class="form-layout">
            <!-- 左侧表单 -->
            <div class="form-left">
              <!-- 人格名称 -->
              <div class="form-item">
                <input
                  v-model="formData.prompt_name"
                  type="text"
                  class="form-input"
                  :placeholder="$t('personality.promptName') || '人格名称'"
                />
              </div>

              <!-- 系统提示词 -->
              <div class="form-item">
                <textarea
                  v-model="formData.system_prompt"
                  class="form-textarea"
                  :placeholder="$t('personality.systemPrompt') || '系统提示词'"
                  rows="12"
                ></textarea>
              </div>

              <!-- 描述 -->
              <div class="form-item">
                <input
                  v-model="formData.description"
                  type="text"
                  class="form-input"
                  :placeholder="
                    $t('personality.customErrorMessage') ||
                    '自定义报错回复信息（可选）'
                  "
                />
              </div>
            </div>

            <!-- 右侧配置 -->
            <div class="form-right">
              <!-- 工具/MCP 工具选择 -->
              <div class="config-section">
                <div class="section-header" @click="toggleSection('tools')">
                  <div class="section-title">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path
                        d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z"
                      />
                    </svg>
                    <span>{{
                      $t("personality.toolSelection") || "工具 / MCP 工具选择"
                    }}</span>
                  </div>
                  <svg
                    class="expand-icon"
                    :class="{ expanded: expandedSections.tools }"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path
                      d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"
                    />
                  </svg>
                </div>
                <div v-show="expandedSections.tools" class="section-content">
                  <p class="section-desc">
                    {{
                      $t("personality.toolDesc") ||
                      "为这个人格选择可用的外部工具。外部工具给了 AI 接触外部环境的能力，如搜索、计算、获取信息等。"
                    }}
                  </p>
                  <div class="radio-group">
                    <label class="radio-item">
                      <input
                        v-model="toolSelectionMode"
                        type="radio"
                        value="all"
                      />
                      <span>{{
                        $t("personality.useAllTools") || "默认使用全部函数工具"
                      }}</span>
                    </label>
                    <label class="radio-item">
                      <input
                        v-model="toolSelectionMode"
                        type="radio"
                        value="custom"
                      />
                      <span>{{
                        $t("personality.selectCustomTools") ||
                        "选择指定函数工具"
                      }}</span>
                    </label>
                  </div>
                </div>
              </div>

              <!-- Skills 选择 -->
              <div class="config-section">
                <div class="section-header" @click="toggleSection('skills')">
                  <div class="section-title">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M7 2v11h3v9l7-12h-4l4-8z" />
                    </svg>
                    <span
                      >Skills {{ $t("personality.selection") || "选择" }}</span
                    >
                  </div>
                  <svg
                    class="expand-icon"
                    :class="{ expanded: expandedSections.skills }"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path
                      d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"
                    />
                  </svg>
                </div>
                <div v-show="expandedSections.skills" class="section-content">
                  <p class="section-desc">
                    {{
                      $t("personality.skillsDesc") ||
                      "为这个人格选择可用的 Skills。Skills 会给 AI 提供可复用的流程与规范。"
                    }}
                  </p>
                  <div class="radio-group">
                    <label class="radio-item">
                      <input type="radio" checked disabled />
                      <span>{{
                        $t("personality.useAllSkills") || "默认使用全部 Skills"
                      }}</span>
                    </label>
                    <label class="radio-item disabled">
                      <input type="radio" disabled />
                      <span>{{
                        $t("personality.selectCustomSkills") ||
                        "选择指定 Skills"
                      }}</span>
                    </label>
                  </div>
                </div>
              </div>

              <!-- 预设对话 -->
              <div class="config-section">
                <div class="section-header" @click="toggleSection('dialogues')">
                  <div class="section-title">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path
                        d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"
                      />
                    </svg>
                    <span>{{
                      $t("personality.presetDialogues") || "预设对话"
                    }}</span>
                  </div>
                  <svg
                    class="expand-icon"
                    :class="{ expanded: expandedSections.dialogues }"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path
                      d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"
                    />
                  </svg>
                </div>
                <div
                  v-show="expandedSections.dialogues"
                  class="section-content"
                >
                  <p class="section-desc">
                    {{
                      $t("personality.dialogueDesc") ||
                      "添加一些预设的对话来帮助机器人更好地理解角色设定。"
                    }}
                  </p>

                  <!-- 对话列表 -->
                  <div class="dialogue-list">
                    <div
                      v-for="(dialogue, index) in dialogues"
                      :key="index"
                      class="dialogue-item"
                    >
                      <div class="dialogue-role">
                        {{ dialogue.role === "user" ? "User" : "Assistant" }}
                      </div>
                      <textarea
                        v-model="dialogue.content"
                        class="dialogue-input"
                        :placeholder="
                          dialogue.role === 'user'
                            ? $t('personality.userMessage') || '用户消息...'
                            : $t('personality.assistantMessage') ||
                              '助手回复...'
                        "
                        rows="2"
                      ></textarea>
                      <button
                        class="dialogue-remove"
                        @click="removeDialogue(index)"
                      >
                        <svg viewBox="0 0 24 24" fill="currentColor">
                          <path
                            d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
                          />
                        </svg>
                      </button>
                    </div>
                  </div>

                  <!-- 添加对话按钮 -->
                  <button class="add-dialogue-btn" @click="addDialoguePair">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
                    </svg>
                    {{ $t("personality.addDialoguePair") || "添加对话对" }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部按钮 -->
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">
            {{ $t("common.cancel") || "取消" }}
          </button>
          <button class="btn btn-primary" @click="handleSubmit">
            {{ $t("common.save") || "保存" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
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

.modal-container {
  background: var(--bg-primary);
  border-radius: 12px;
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
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
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 6px;
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
  padding: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
}

/* 文件夹提示 */
.folder-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #e6f7ff;
  border-radius: 8px;
  margin-bottom: 20px;
  color: #1890ff;
  font-size: 13px;
}

.folder-hint svg {
  width: 16px;
  height: 16px;
}

/* 表单布局 */
.form-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.form-left,
.form-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
}

.form-input,
.form-textarea {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
  outline: none;
  transition: all 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  border-color: var(--primary-color);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: var(--text-tertiary);
}

.form-textarea {
  resize: vertical;
  min-height: 200px;
  font-family: inherit;
  line-height: 1.6;
}

/* 配置区块 */
.config-section {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: var(--bg-secondary);
  cursor: pointer;
  transition: background 0.2s;
}

.section-header:hover {
  background: var(--bg-hover);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.section-title svg {
  width: 18px;
  height: 18px;
  color: var(--text-secondary);
}

.expand-icon {
  width: 20px;
  height: 20px;
  color: var(--text-tertiary);
  transition: transform 0.2s;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.section-content {
  padding: 16px;
}

.section-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0 0 16px 0;
  line-height: 1.5;
}

/* 单选组 */
.radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
}

.radio-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.radio-item input[type="radio"] {
  width: 16px;
  height: 16px;
  accent-color: var(--primary-color);
}

/* 对话列表 */
.dialogue-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.dialogue-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.dialogue-role {
  width: 70px;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  padding-top: 10px;
}

.dialogue-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  background: var(--bg-primary);
  color: var(--text-primary);
  outline: none;
  resize: vertical;
  font-family: inherit;
}

.dialogue-input:focus {
  border-color: var(--primary-color);
}

.dialogue-remove {
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
  flex-shrink: 0;
  margin-top: 4px;
}

.dialogue-remove:hover {
  background: var(--bg-hover);
  color: #ff4d4f;
}

.dialogue-remove svg {
  width: 16px;
  height: 16px;
}

/* 添加对话按钮 */
.add-dialogue-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 10px;
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.add-dialogue-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: var(--primary-light);
}

.add-dialogue-btn svg {
  width: 16px;
  height: 16px;
}

/* 底部按钮 */
.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background: transparent;
  color: var(--text-secondary);
}

.btn-secondary:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
</style>
