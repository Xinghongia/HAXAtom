<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { t } from "../../../locales";
import { pluginApi } from "../../../api/plugin";

const $t = computed(() => t);

const loading = ref(false);
const plugins = ref<any[]>([]);

const pluginsBySource = computed(() => {
  const groups: Record<string, Plugin[]> = {
    builtin: [],
    skill: [],
    mcp: [],
    community: [],
  };
  plugins.value.forEach((p) => {
    if (groups[p.source]) {
      groups[p.source].push(p);
    } else {
      groups.community.push(p);
    }
  });
  return groups;
});

const sourceLabels: Record<string, string> = {
  builtin: "内置",
  skill: "Skill",
  mcp: "MCP",
  community: "社区",
};

const sourceColors: Record<string, string> = {
  builtin: "#67c23a",
  skill: "#409eff",
  mcp: "#e6a23c",
  community: "#909399",
};

const loadPlugins = async () => {
  loading.value = true;
  try {
    const res = await pluginApi.list();
    plugins.value = (res as any).data || [];
  } catch (error) {
    console.error("加载插件失败:", error);
  } finally {
    loading.value = false;
  }
};

const togglePlugin = async (plugin: any) => {
  try {
    if (plugin.enabled) {
      await pluginApi.disable(plugin.id);
    } else {
      await pluginApi.enable(plugin.id);
    }
    plugin.enabled = !plugin.enabled;
  } catch (error) {
    console.error("切换插件状态失败:", error);
  }
};

const getPluginIcon = (plugin: Plugin): string => {
  if (plugin.icon) return plugin.icon;
  switch (plugin.source) {
    case "builtin":
      return "🧰";
    case "skill":
      return "⚡";
    case "mcp":
      return "🔌";
    default:
      return "📦";
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
      <p>{{ $t("bot.plugins.subtitle") || "管理 HAXAtom 插件资源" }}</p>
    </div>

    <div class="page-content">
      <div v-if="loading" class="loading-state">
        <span>加载中...</span>
      </div>

      <template v-else>
        <!-- 内置插件 -->
        <div v-if="pluginsBySource.builtin.length > 0" class="plugin-section">
          <div class="section-header">
            <h3>内置插件</h3>
            <span class="section-count">{{
              pluginsBySource.builtin.length
            }}</span>
          </div>
          <div class="plugin-grid">
            <div
              v-for="plugin in pluginsBySource.builtin"
              :key="plugin.id"
              class="plugin-card"
              :class="{ disabled: !plugin.enabled }"
            >
              <div class="plugin-icon">{{ getPluginIcon(plugin) }}</div>
              <div class="plugin-info">
                <div class="plugin-name">{{ plugin.name }}</div>
                <div class="plugin-desc">{{ plugin.description }}</div>
              </div>
              <div class="plugin-actions">
                <span
                  class="source-badge"
                  :style="{ backgroundColor: sourceColors[plugin.source] }"
                >
                  {{ sourceLabels[plugin.source] }}
                </span>
                <label class="toggle-switch">
                  <input
                    type="checkbox"
                    :checked="plugin.enabled"
                    @change="togglePlugin(plugin)"
                  />
                  <span class="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Skill 插件 -->
        <div v-if="pluginsBySource.skill.length > 0" class="plugin-section">
          <div class="section-header">
            <h3>Skills</h3>
            <span class="section-count">{{
              pluginsBySource.skill.length
            }}</span>
          </div>
          <div class="plugin-grid">
            <div
              v-for="plugin in pluginsBySource.skill"
              :key="plugin.id"
              class="plugin-card"
              :class="{ disabled: !plugin.enabled }"
            >
              <div class="plugin-icon">{{ getPluginIcon(plugin) }}</div>
              <div class="plugin-info">
                <div class="plugin-name">{{ plugin.name }}</div>
                <div class="plugin-desc">{{ plugin.description }}</div>
              </div>
              <div class="plugin-actions">
                <span
                  class="source-badge"
                  :style="{ backgroundColor: sourceColors[plugin.source] }"
                >
                  {{ sourceLabels[plugin.source] }}
                </span>
                <label class="toggle-switch">
                  <input
                    type="checkbox"
                    :checked="plugin.enabled"
                    @change="togglePlugin(plugin)"
                  />
                  <span class="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- MCP 插件 -->
        <div v-if="pluginsBySource.mcp.length > 0" class="plugin-section">
          <div class="section-header">
            <h3>MCP</h3>
            <span class="section-count">{{ pluginsBySource.mcp.length }}</span>
          </div>
          <div class="plugin-grid">
            <div
              v-for="plugin in pluginsBySource.mcp"
              :key="plugin.id"
              class="plugin-card"
              :class="{ disabled: !plugin.enabled }"
            >
              <div class="plugin-icon">{{ getPluginIcon(plugin) }}</div>
              <div class="plugin-info">
                <div class="plugin-name">{{ plugin.name }}</div>
                <div class="plugin-desc">{{ plugin.description }}</div>
              </div>
              <div class="plugin-actions">
                <span
                  class="source-badge"
                  :style="{ backgroundColor: sourceColors[plugin.source] }"
                >
                  {{ sourceLabels[plugin.source] }}
                </span>
                <label class="toggle-switch">
                  <input
                    type="checkbox"
                    :checked="plugin.enabled"
                    @change="togglePlugin(plugin)"
                  />
                  <span class="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- 社区插件 -->
        <div v-if="pluginsBySource.community.length > 0" class="plugin-section">
          <div class="section-header">
            <h3>社区插件</h3>
            <span class="section-count">{{
              pluginsBySource.community.length
            }}</span>
          </div>
          <div class="plugin-grid">
            <div
              v-for="plugin in pluginsBySource.community"
              :key="plugin.id"
              class="plugin-card"
              :class="{ disabled: !plugin.enabled }"
            >
              <div class="plugin-icon">{{ getPluginIcon(plugin) }}</div>
              <div class="plugin-info">
                <div class="plugin-name">{{ plugin.name }}</div>
                <div class="plugin-desc">{{ plugin.description }}</div>
              </div>
              <div class="plugin-actions">
                <span
                  class="source-badge"
                  :style="{ backgroundColor: sourceColors[plugin.source] }"
                >
                  {{ sourceLabels[plugin.source] }}
                </span>
                <label class="toggle-switch">
                  <input
                    type="checkbox"
                    :checked="plugin.enabled"
                    @change="togglePlugin(plugin)"
                  />
                  <span class="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="plugins.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"
            />
          </svg>
          <span>暂无插件</span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.plugins-page {
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

.plugin-section {
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

.plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.plugin-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  transition: all 0.2s ease;
}

.plugin-card:hover {
  border-color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.plugin-card.disabled .toggle-slider {
  background-color: #e5e7eb;
}

.plugin-card.disabled .toggle-slider:before {
  background-color: #d1d5db;
}

.plugin-icon {
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

.plugin-info {
  flex: 1;
  min-width: 0;
}

.plugin-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plugin-desc {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plugin-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.source-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  color: white;
  font-weight: 500;
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
</style>
