<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { t } from "../../../locales";
import { botApi, channelTypeLabels, channelTypeColors, type BotResponse, type ChannelType } from "../../../api/bot";
import { getPresets, type PresetListItem } from "../../../api/preset";

const $t = computed(() => t);

const bots = ref<BotResponse[]>([]);
const presets = ref<PresetListItem[]>([]);
const loading = ref(false);

// Modal state
const showModal = ref(false);
const editingBot = ref<BotResponse | null>(null);
const formData = ref({
  bot_id: "",
  bot_name: "",
  channel_type: "onebot11" as ChannelType,
  preset_id: "",
  is_active: true,
});

// Load bots and presets
const loadData = async () => {
  loading.value = true;
  try {
    const [botsRes, presetsRes] = await Promise.all([
      botApi.list(),
      getPresets(),
    ]);
    bots.value = (botsRes as any).data || [];
    presets.value = (presetsRes as any).data || [];
  } catch (error) {
    console.error("加载数据失败:", error);
  } finally {
    loading.value = false;
  }
};

// Group bots by channel type
const botsByChannel = computed(() => {
  const groups: Record<string, BotResponse[]> = {};
  bots.value.forEach((bot) => {
    if (!groups[bot.channel_type]) {
      groups[bot.channel_type] = [];
    }
    groups[bot.channel_type].push(bot);
  });
  return groups;
});

const getPresetName = (presetId: string): string => {
  const preset = presets.value.find((p) => p.preset_id === presetId);
  return preset?.preset_name || presetId;
};

const openCreateModal = () => {
  editingBot.value = null;
  formData.value = {
    bot_id: "",
    bot_name: "",
    channel_type: "onebot11",
    preset_id: presets.value[0]?.preset_id || "",
    is_active: true,
  };
  showModal.value = true;
};

const openEditModal = (bot: BotResponse) => {
  editingBot.value = bot;
  formData.value = {
    bot_id: bot.bot_id,
    bot_name: bot.bot_name,
    channel_type: bot.channel_type,
    preset_id: bot.preset_id,
    is_active: bot.is_active,
  };
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  editingBot.value = null;
};

const handleSubmit = async () => {
  try {
    if (editingBot.value) {
      await botApi.update(editingBot.value.bot_id, {
        bot_name: formData.value.bot_name,
        preset_id: formData.value.preset_id,
        is_active: formData.value.is_active,
      });
    } else {
      await botApi.create(formData.value);
    }
    closeModal();
    await loadData();
  } catch (error) {
    console.error("保存失败:", error);
    alert("保存失败");
  }
};

const handleDelete = async (botId: string) => {
  if (!confirm("确定要删除这个机器人吗？")) return;
  try {
    await botApi.delete(botId);
    await loadData();
  } catch (error) {
    console.error("删除失败:", error);
  }
};

const toggleBot = async (bot: BotResponse) => {
  try {
    await botApi.update(bot.bot_id, { is_active: !bot.is_active });
    bot.is_active = !bot.is_active;
  } catch (error) {
    console.error("切换状态失败:", error);
  }
};

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="bot-page">
    <div class="page-header">
      <h1>{{ $t("bot.bot.title") || "机器人管理" }}</h1>
      <p>{{ $t("bot.bot.subtitle") || "管理多渠道机器人配置" }}</p>
    </div>

    <div class="page-content">
      <div v-if="loading" class="loading-state">
        <span>加载中...</span>
      </div>

      <template v-else>
        <!-- 工具栏 -->
        <div class="toolbar">
          <button class="btn btn-primary" @click="openCreateModal">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
            </svg>
            添加机器人
          </button>
        </div>

        <!-- 按渠道分组显示 -->
        <div v-for="(channelBots, channelType) in botsByChannel" :key="channelType" class="bot-section">
          <div class="section-header">
            <h3>{{ channelTypeLabels[channelType as ChannelType] || channelType }}</h3>
            <span class="section-count">{{ channelBots.length }}</span>
          </div>
          <div class="bot-grid">
            <div
              v-for="bot in channelBots"
              :key="bot.bot_id"
              class="bot-card"
              :class="{ disabled: !bot.is_active }"
            >
              <div class="bot-icon">
                {{ channelType === 'onebot11' ? '🤖' : channelType === 'feishu' ? '📱' : channelType === 'telegram' ? '✈️' : '💬' }}
              </div>
              <div class="bot-info">
                <div class="bot-name">{{ bot.bot_name }}</div>
                <div class="bot-preset">预设: {{ getPresetName(bot.preset_id) }}</div>
              </div>
              <div class="bot-actions">
                <span
                  class="channel-badge"
                  :style="{ backgroundColor: channelTypeColors[channelType as ChannelType] }"
                >
                  {{ channelTypeLabels[channelType as ChannelType] }}
                </span>
                <label class="toggle-switch">
                  <input type="checkbox" :checked="bot.is_active" @change="toggleBot(bot)" />
                  <span class="toggle-slider"></span>
                </label>
              </div>
              <div class="bot-operations">
                <button class="btn-icon" @click="openEditModal(bot)" title="编辑">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
                  </svg>
                </button>
                <button class="btn-icon delete" @click="handleDelete(bot.bot_id)" title="删除">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="bots.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 9V7c0-1.1-.9-2-2-2h-3c0-1.66-1.34-3-3-3S9 3.34 9 5H6c-1.1 0-2 .9-2 2v2c-1.1 0-2 .9-2 2v7c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-7c0-1.1-.9-2-2-2z" />
          </svg>
          <span>暂无机器人，点击"添加机器人"创建</span>
        </div>
      </template>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingBot ? "编辑机器人" : "添加机器人" }}</h3>
          <button class="btn-close" @click="closeModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>机器人 ID</label>
            <input
              v-model="formData.bot_id"
              type="text"
              :disabled="!!editingBot"
              placeholder="唯一标识，如: my-bot-001"
            />
          </div>
          <div class="form-group">
            <label>机器人名称</label>
            <input v-model="formData.bot_name" type="text" placeholder="显示名称" />
          </div>
          <div class="form-group">
            <label>渠道类型</label>
            <select v-model="formData.channel_type" :disabled="!!editingBot">
              <option value="onebot11">OneBot v11</option>
              <option value="feishu">飞书</option>
              <option value="dingtalk">钉钉</option>
              <option value="telegram">Telegram</option>
              <option value="qqofficial">QQ 官方</option>
            </select>
          </div>
          <div class="form-group">
            <label>关联预设</label>
            <select v-model="formData.preset_id">
              <option v-for="preset in presets" :key="preset.preset_id" :value="preset.preset_id">
                {{ preset.preset_name }}
              </option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="handleSubmit">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bot-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px 32px;
  overflow-y: auto;
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
  gap: 24px;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-secondary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 16px;
  color: var(--text-secondary);
}

.empty-state svg {
  width: 64px;
  height: 64px;
  opacity: 0.5;
}

.toolbar {
  display: flex;
  gap: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
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
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: var(--border-color);
}

.btn svg {
  width: 18px;
  height: 18px;
}

.bot-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-count {
  font-size: 12px;
  padding: 2px 8px;
  background: var(--bg-secondary);
  border-radius: 10px;
  color: var(--text-secondary);
}

.bot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.bot-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  transition: all 0.2s ease;
}

.bot-card:hover {
  border-color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.bot-card.disabled .toggle-slider {
  background-color: #e5e7eb;
}

.bot-card.disabled .toggle-slider:before {
  background-color: #d1d5db;
}

.bot-icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: 8px;
  flex-shrink: 0;
}

.bot-info {
  flex: 1;
  min-width: 0;
}

.bot-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.bot-preset {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bot-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.channel-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  color: white;
  font-weight: 500;
}

.bot-operations {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.btn-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.btn-icon:hover {
  background: var(--bg-secondary);
  color: var(--primary-color);
}

.btn-icon.delete:hover {
  color: #f56c6c;
}

.btn-icon svg {
  width: 16px;
  height: 16px;
}

.toggle-switch {
  position: relative;
  width: 36px;
  height: 20px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-secondary);
  border-radius: 20px;
  transition: 0.3s;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 14px;
  width: 14px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  border-radius: 50%;
  transition: 0.3s;
}

.toggle-switch input:checked + .toggle-slider {
  background-color: var(--primary-color);
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(16px);
}

/* Modal */
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

.modal {
  background: var(--bg-card);
  border-radius: 12px;
  width: 480px;
  max-width: 90%;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.btn-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--text-secondary);
  border-radius: 4px;
}

.btn-close:hover {
  background: var(--bg-secondary);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input,
.form-group select {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-card);
  color: var(--text-primary);
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.form-group input:disabled {
  background: var(--bg-secondary);
  cursor: not-allowed;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}
</style>