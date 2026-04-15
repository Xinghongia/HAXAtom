/**
 * 路由配置
 *
 * 使用 Vue Router 4 + TypeScript
 */

import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: "/",
    redirect: "/bot",
  },
  {
    path: "/bot",
    name: "Bot",
    component: () => import("../views/bot/BotView.vue"),
    redirect: "/bot/welcome",
    meta: {
      title: "机器人配置",
      showSidebarToggle: true,
    },
    children: [
      {
        path: "welcome",
        name: "BotWelcome",
        component: () => import("../views/bot/pages/WelcomePage.vue"),
        meta: { title: "欢迎" },
      },
      {
        path: "model",
        name: "BotModel",
        component: () => import("../views/bot/pages/ModelProviderView.vue"),
        meta: { title: "模型提供商" },
      },
      {
        path: "personality",
        name: "BotPersonality",
        component: () => import("../views/bot/pages/PersonalityView.vue"),
        meta: { title: "人格设定" },
      },
      // 对话数据页面
      {
        path: "chat-data",
        name: "BotChatData",
        component: () => import("../views/bot/pages/ChatDataPage.vue"),
        meta: { title: "对话数据" },
      },
      {
        path: "bot",
        name: "BotManagement",
        component: () => import("../views/bot/pages/BotPage.vue"),
        meta: { title: "机器人管理" },
      },
      // {
      //   path: "future-tasks",
      //   name: "BotFutureTasks",
      //   component: () => import("../views/bot/pages/FutureTasksPage.vue"),
      //   meta: { title: "未来任务" },
      // },
      // {
      //   path: "subagent",
      //   name: "BotSubAgent",
      //   component: () => import("../views/bot/pages/SubAgentPage.vue"),
      //   meta: { title: "SubAgent 编排" },
      // },
      // {
      //   path: "data-stats",
      //   name: "BotDataStats",
      //   component: () => import("../views/bot/pages/DataStatsPage.vue"),
      //   meta: { title: "数据统计" },
      // },
      {
        path: "platform-logs",
        name: "BotPlatformLogs",
        component: () => import("../views/bot/pages/PlatformLogs.vue"),
        meta: { title: "平台日志" },
      },
      // {
      //   path: "tracking",
      //   name: "BotTracking",
      //   component: () => import("../views/bot/pages/TrackingPage.vue"),
      //   meta: { title: "追踪" },
      // },
      {
        path: "knowledge",
        name: "BotKnowledge",
        component: () => import("../views/bot/pages/KnowledgeBasePage.vue"),
        meta: { title: "知识库" },
      },
      {
        path: "preset",
        name: "BotPreset",
        component: () => import("../views/bot/pages/PresetPage.vue"),
        meta: { title: "预设方案" },
      },
      {
        path: "plugins",
        name: "BotAstrBotPlugins",
        component: () => import("../views/bot/pages/PluginsPage.vue"),
        meta: { title: "HAXAtom 插件" },
      },
      // {
      //   path: "plugin-market",
      //   name: "BotPluginMarket",
      //   component: () => import("../views/bot/pages/PluginMarketPage.vue"),
      //   meta: { title: "插件市场" },
      // },
      // {
      //   path: "mcp",
      //   name: "BotMcp",
      //   component: () => import("../views/bot/pages/McpPage.vue"),
      //   meta: { title: "MCP" },
      // },
      // {
      //   path: "skills",
      //   name: "BotSkills",
      //   component: () => import("../views/bot/pages/SkillsPage.vue"),
      //   meta: { title: "Skills" },
      // },
      {
        path: "memory",
        name: "BotMemory",
        component: () => import("../views/bot/pages/MemoryConfigPage.vue"),
        meta: { title: "记忆配置" },
      },
      {
        path: "settings",
        name: "BotSettings",
        component: () => import("../views/bot/pages/SettingsPage.vue"),
        meta: { title: "系统设置" },
      },
      {
        path: "changelog",
        name: "BotChangelog",
        component: () => import("../views/bot/pages/ChangelogPage.vue"),
        meta: { title: "更新日志" },
      },
    ],
  },
  {
    path: "/chat",
    name: "Chat",
    component: () => import("../views/chat/ChatView.vue"),
    meta: {
      title: "对话",
      showSidebarToggle: false,
    },
  },
  {
    path: "/chat/:sessionId",
    name: "ChatWithSession",
    component: () => import("../views/chat/ChatView.vue"),
    meta: {
      title: "对话",
      showSidebarToggle: false,
    },
  },
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - HAXAtom`;
  }
  next();
});

export default router;
