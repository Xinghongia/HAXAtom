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
    meta: {
      title: "机器人配置",
      showSidebarToggle: true,
    },
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
