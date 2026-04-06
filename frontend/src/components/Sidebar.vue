<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { t } from "../locales";

const props = defineProps<{
  collapsed?: boolean;
  activeRoute?: string;
}>();

const router = useRouter();
const route = useRoute();

const $t = computed(() => t);

// 跟踪菜单展开状态
const expandedMenus = ref({
  config: false,
  plugin: false,
  more: false,
});

// 切换菜单展开状态
const toggleMenu = (menuKey: string) => {
  if (
    expandedMenus.value.hasOwnProperty(
      menuKey as keyof typeof expandedMenus.value,
    )
  ) {
    expandedMenus.value[menuKey as keyof typeof expandedMenus.value] =
      !expandedMenus.value[menuKey as keyof typeof expandedMenus.value];
  }
};

// 导航到指定路由
const navigateTo = (routeName: string) => {
  router.push({ name: routeName });
};

// 判断当前路由是否激活
const isActive = (routeName: string) => {
  return route.name === routeName;
};

// 打开外部链接
const openExternalUrl = (url: string) => {
  window.open(url, "_blank");
};

const menuItems = [
  {
    icon: "welcome",
    label: computed(() => $t.value("bot.sidebar.welcome") || "欢迎"),
    routeName: "BotWelcome",
  },
  {
    icon: "bot",
    label: computed(() => $t.value("bot.sidebar.bot") || "机器人"),
    routeName: "BotManagement",
  },
  {
    icon: "model",
    label: computed(() => $t.value("bot.sidebar.models") || "模型提供商"),
    routeName: "BotModel",
  },
  {
    icon: "preset",
    label: computed(() => $t.value("bot.sidebar.preset") || "预设方案"),
    routeName: "BotPreset",
  },
  {
    icon: "plugin",
    label: computed(() => $t.value("bot.sidebar.plugins") || "插件"),
    expandable: true,
    menuKey: "plugin",
    children: [
      {
        icon: "plugin",
        label: computed(
          () => $t.value("bot.sidebar.haxatomPlugins") || "HAXAtom 插件",
        ),
        routeName: "BotAstrBotPlugins",
      },
      {
        icon: "market",
        label: computed(
          () => $t.value("bot.sidebar.pluginMarket") || "插件市场",
        ),
        routeName: "BotPluginMarket",
      },
      {
        icon: "mcp",
        label: computed(() => $t.value("bot.sidebar.mcp") || "MCP"),
        routeName: "BotMcp",
      },
      {
        icon: "skills",
        label: computed(() => $t.value("bot.sidebar.skills") || "Skills"),
        routeName: "BotSkills",
      },
    ],
  },
  {
    icon: "knowledge",
    label: computed(() => $t.value("bot.sidebar.knowledge") || "知识库"),
    routeName: "BotKnowledge",
  },
  {
    icon: "personality",
    label: computed(() => $t.value("bot.sidebar.personality") || "人格设定"),
    routeName: "BotPersonality",
  },
  {
    icon: "memory",
    label: computed(() => $t.value("bot.sidebar.memory") || "记忆配置"),
    routeName: "BotMemory",
  },
  {
    icon: "more",
    label: computed(() => $t.value("bot.sidebar.more") || "更多功能"),
    expandable: true,
    menuKey: "more",
    children: [
      {
        icon: "database",
        label: computed(() => $t.value("bot.sidebar.chatData") || "对话数据"),
        routeName: "BotChatData",
      },
      {
        icon: "rules",
        label: computed(
          () => $t.value("bot.sidebar.customRules") || "自定义规则",
        ),
        routeName: "BotCustomRules",
      },
      {
        icon: "schedule",
        label: computed(
          () => $t.value("bot.sidebar.futureTasks") || "未来任务",
        ),
        routeName: "BotFutureTasks",
      },
      {
        icon: "subagent",
        label: computed(
          () => $t.value("bot.sidebar.subAgent") || "SubAgent 编排",
        ),
        routeName: "BotSubAgent",
      },
      {
        icon: "stats",
        label: computed(() => $t.value("bot.sidebar.dataStats") || "数据统计"),
        routeName: "BotDataStats",
      },
      {
        icon: "logs",
        label: computed(
          () => $t.value("bot.sidebar.platformLogs") || "平台日志",
        ),
        routeName: "BotPlatformLogs",
      },
      {
        icon: "tracking",
        label: computed(() => $t.value("bot.sidebar.tracking") || "追踪"),
        routeName: "BotTracking",
      },
    ],
  },
];

const bottomItems = [
  {
    icon: "settings",
    label: computed(() => $t.value("settings.settings") || "设置"),
  },
  {
    icon: "changelog",
    label: computed(() => $t.value("sidebar.changelog") || "更新日志"),
  },
  {
    icon: "docs",
    label: computed(() => $t.value("sidebar.docs") || "官方文档"),
  },
  { icon: "faq", label: "FAQ" },
  {
    icon: "github",
    label: "GitHub",
    url: "https://github.com/guhong521/HAXAtom",
  },
];
</script>

<template>
  <aside class="sidebar" :class="{ collapsed }">
    <!-- 菜单列表 -->
    <nav class="menu-list">
      <div
        v-for="(item, index) in menuItems"
        :key="index"
        class="menu-item-wrapper"
      >
        <div
          class="menu-item"
          :class="{
            active: isActive(item.routeName),
            expandable: item.expandable,
            expanded:
              item.menuKey &&
              expandedMenus[item.menuKey as keyof typeof expandedMenus],
          }"
          @click="
            item.expandable
              ? toggleMenu(item.menuKey!)
              : item.routeName
                ? navigateTo(item.routeName)
                : undefined
          "
        >
          <div class="menu-content">
            <svg class="menu-icon" viewBox="0 0 24 24" fill="currentColor">
              <!-- 欢迎/首页 -->
              <g v-if="item.icon === 'welcome'">
                <path
                  d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"
                />
              </g>
              <!-- 机器人 -->
              <g v-else-if="item.icon === 'bot'">
                <path
                  d="M20 9V7c0-1.1-.9-2-2-2h-3c0-1.66-1.34-3-3-3S9 3.34 9 5H6c-1.1 0-2 .9-2 2v2c-1.1 0-2 .9-2 2v7c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-7c0-1.1-.9-2-2-2zm-7-3c.55 0 1 .45 1 1v1h-2V7c0-.55.45-1 1-1zM4 11h16v7H4v-7zm4 5c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm8 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"
                />
              </g>
              <!-- 模型提供商 -->
              <g v-else-if="item.icon === 'model'">
                <path
                  d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                />
              </g>
              <!-- 人格设定 -->
              <g v-else-if="item.icon === 'personality'">
                <path
                  d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
                />
              </g>
              <!-- 知识库 -->
              <g v-else-if="item.icon === 'knowledge'">
                <path
                  d="M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09V17h2V9L12 3zm6.82 6L12 12.72 5.18 9 12 5.28 18.82 9zM17 15.99l-5 2.73-5-2.73v-3.72L12 15l5-2.73v3.72z"
                />
              </g>
              <!-- 预设方案 -->
              <g v-else-if="item.icon === 'preset'">
                <path
                  d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z"
                />
              </g>
              <!-- 记忆配置 -->
              <g v-else-if="item.icon === 'memory'">
                <path
                  d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"
                />
              </g>
              <!-- 插件 -->
              <g v-else-if="item.icon === 'plugin'">
                <path
                  d="M20.5 11H19V7c0-1.1-.9-2-2-2h-4V3.5C13 2.12 11.88 1 10.5 1S8 2.12 8 3.5V5H4c-1.1 0-1.99.9-1.99 2v3.8H3.5c1.49 0 2.7 1.21 2.7 2.7s-1.21 2.7-2.7 2.7H2V20c0 1.1.9 2 2 2h3.8v-1.5c0-1.49 1.21-2.7 2.7-2.7s2.7 1.21 2.7 2.7V22H17c1.1 0 2-.9 2-2v-4h1.5c1.38 0 2.5-1.12 2.5-2.5S21.88 11 20.5 11z"
                />
              </g>
              <!-- 更多功能 -->
              <g v-else-if="item.icon === 'more'">
                <path
                  d="M6 10c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm12 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"
                />
              </g>
            </svg>
            <span class="menu-label" v-if="!collapsed">{{ item.label }}</span>
            <svg
              v-if="item.expandable && !collapsed"
              class="expand-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M6 9l6 6 6-6" />
            </svg>
          </div>
          <!-- 二级菜单 -->
          <div
            v-show="
              item.children &&
              expandedMenus[item.menuKey as keyof typeof expandedMenus] &&
              !collapsed
            "
            class="submenu"
            :class="{
              'submenu-collapsed':
                !expandedMenus[item.menuKey as keyof typeof expandedMenus],
            }"
          >
            <div class="submenu-content">
              <div
                v-for="(child, childIndex) in item.children"
                :key="childIndex"
                class="submenu-item"
                :class="{ active: isActive(child.routeName) }"
                @click.stop="child.routeName && navigateTo(child.routeName)"
              >
                <svg
                  class="submenu-icon"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <!-- 对话数据 -->
                  <g v-if="child.icon === 'database'">
                    <path
                      d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"
                    />
                  </g>
                  <!-- 自定义规则 -->
                  <g v-else-if="child.icon === 'rules'">
                    <path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z" />
                  </g>
                  <!-- 未来任务 -->
                  <g v-else-if="child.icon === 'schedule'">
                    <path
                      d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"
                    />
                  </g>
                  <!-- SubAgent 编排 -->
                  <g v-else-if="child.icon === 'subagent'">
                    <path
                      d="M17 16l-4-4V8.82C14.16 8.4 15 7.3 15 6c0-1.66-1.34-3-3-3S9 4.34 9 6c0 1.3.84 2.4 2 2.82V12l-4 4H3v3h3v-1.18l3.64-3.64 1.41 1.41L8.41 19H7v2h3v-1.18l3.64-3.64 1.41 1.41L12.41 19H11v2h3v-1.18l3.64-3.64 1.41 1.41L16.41 19H15v2h3v-3h-1z"
                    />
                  </g>
                  <!-- 数据统计 -->
                  <g v-else-if="child.icon === 'stats'">
                    <path
                      d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"
                    />
                  </g>
                  <!-- 平台日志 -->
                  <g v-else-if="child.icon === 'logs'">
                    <path
                      d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"
                    />
                  </g>
                  <!-- 追踪 -->
                  <g v-else-if="child.icon === 'tracking'">
                    <path
                      d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-5.5-2.5l7.51-3.22-7.52-3.22 3.01 3.22zm5.5-11c-3.03 0-5.5 2.47-5.5 5.5 0 1.44.56 2.75 1.47 3.72l.08.07c.17.15.35.29.54.42l.03.02c.26.19.54.36.84.49.04.02.08.04.12.05.27.11.56.19.85.24.08.01.16.02.24.03.26.04.53.06.8.06h.03c.27 0 .54-.02.8-.06.08-.01.16-.02.24-.03.29-.05.58-.13.85-.24.04-.01.08-.03.12-.05.3-.13.58-.3.84-.49l.03-.02c.19-.13.37-.27.54-.42l.08-.07c.91-.97 1.47-2.28 1.47-3.72 0-3.03-2.47-5.5-5.5-5.5z"
                    />
                  </g>
                  <!-- AstrBot 插件 -->
                  <g v-else-if="child.icon === 'plugin'">
                    <path
                      d="M20.5 11H19V7c0-1.1-.9-2-2-2h-4V3.5C13 2.12 11.88 1 10.5 1S8 2.12 8 3.5V5H4c-1.1 0-1.99.9-1.99 2v3.8H3.5c1.49 0 2.7 1.21 2.7 2.7s-1.21 2.7-2.7 2.7H2V20c0 1.1.9 2 2 2h3.8v-1.5c0-1.49 1.21-2.7 2.7-2.7s2.7 1.21 2.7 2.7V22H17c1.1 0 2-.9 2-2v-4h1.5c1.38 0 2.5-1.12 2.5-2.5S21.88 11 20.5 11z"
                    />
                  </g>
                  <!-- 插件市场 -->
                  <g v-else-if="child.icon === 'market'">
                    <path
                      d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
                    />
                  </g>
                  <!-- MCP -->
                  <g v-else-if="child.icon === 'mcp'">
                    <path d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z" />
                  </g>
                  <!-- Skills -->
                  <g v-else-if="child.icon === 'skills'">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                  </g>
                </svg>
                <span class="submenu-label">{{ child.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- 底部菜单 -->
    <div class="bottom-menu">
      <div
        v-for="(item, index) in bottomItems"
        :key="index"
        class="bottom-item"
        @click="item.url ? openExternalUrl(item.url) : undefined"
      >
        <svg class="bottom-icon" viewBox="0 0 24 24" fill="currentColor">
          <!-- 设置 -->
          <g v-if="item.icon === 'settings'">
            <path
              d="M19.14 12.94c.04-.32.06-.64.06-.97 0-.33-.02-.66-.06-.97l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96a.488.488 0 0 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.32-.06.65-.06.97s.02.66.06.97l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"
            />
          </g>
          <!-- 更新日志 -->
          <g v-else-if="item.icon === 'changelog'">
            <path
              d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"
            />
          </g>
          <!-- 文档 -->
          <g v-else-if="item.icon === 'docs'">
            <path
              d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"
            />
          </g>
          <!-- FAQ -->
          <g v-else-if="item.icon === 'faq'">
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"
            />
          </g>
          <!-- GitHub -->
          <g v-else-if="item.icon === 'github'">
            <path
              d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z"
            />
          </g>
        </svg>
        <span class="bottom-label" v-if="!collapsed">{{ item.label }}</span>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  height: 100%;
  background: #ffffff;
  border-right: 1px solid var(--border-color, #e5e7eb);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
}

/* 深色模式侧边栏背景 */
html.dark .sidebar {
  background: var(--bg-secondary, #1f2937);
}

.sidebar.collapsed {
  width: 64px;
}

.menu-list {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
}

.menu-item-wrapper {
  margin-bottom: 4px;
}

.menu-item {
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

/* 普通菜单项悬停效果 */
.menu-item:not(.expandable):hover {
  background: var(--bg-hover, #f3f4f6);
}

/* 可展开菜单项 - 只有展开图标有悬停效果 */
.menu-item.expandable .expand-icon {
  transition: all 0.2s ease;
}

.menu-item.expandable:hover .expand-icon {
  color: var(--primary-color, #4f46e5);
}

.menu-item.expandable.expanded:hover .expand-icon {
  transform: rotate(180deg);
}

.menu-item.active {
  background: var(--primary-light, #e0e7ff);
  color: var(--primary-color, #4f46e5);
}

/* 选中状态下的悬停效果保持选中样式 */
.menu-item.active:hover {
  background: var(--primary-light, #e0e7ff);
}

.menu-content {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  gap: 16px;
}

.menu-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: #6b7280;
}

.menu-label {
  flex: 1;
  font-size: 15px;
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expand-icon {
  width: 16px;
  height: 16px;
  transition: transform 0.2s ease;
}

.menu-item.expanded .expand-icon {
  transform: rotate(180deg);
}

/* 子菜单 */
.submenu {
  overflow: hidden;
  transition: all 0.2s ease;
}

.submenu-content {
  padding: 4px 0px;
}

.submenu-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 25px 11px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.submenu-item:hover {
  background: var(--bg-hover, #f3f4f6);
}

.submenu-item.active {
  background: var(--primary-light, #e0e7ff);
  color: var(--primary-color, #4f46e5);
}

.submenu-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: #6b7280;
}

.submenu-label {
  font-size: 14px;
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 底部菜单 */
.bottom-menu {
  padding: 12px 8px;
  border-top: 1px solid var(--border-color, #e5e7eb);
}

.bottom-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.bottom-item:hover {
  background: var(--bg-hover, #f3f4f6);
}

.bottom-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: #6b7280;
}

.bottom-label {
  font-size: 15px;
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 折叠状态 - 保持图标位置固定，不使用 justify-content: center */
.sidebar.collapsed .menu-content,
.sidebar.collapsed .bottom-item {
  justify-content: flex-start;
  padding: 12px 12px;
}

.sidebar.collapsed .menu-icon,
.sidebar.collapsed .bottom-icon {
  margin: 0;
}
</style>
