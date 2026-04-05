<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import Header from "./components/Header.vue";

const route = useRoute();

// 从路由 meta 获取是否显示侧边栏切换按钮
const showSidebarToggle = computed(() => {
  return route.meta.showSidebarToggle as boolean;
});

// 侧边栏折叠状态（全局状态）
const sidebarCollapsed = ref(false);

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value;
};

// 监听路由变化，只在 Bot 页面保持侧边栏状态
const handleRouteChange = () => {
  if (route.name !== "Bot") {
    sidebarCollapsed.value = false;
  }
};

onMounted(() => {
  handleRouteChange();
});

onUnmounted(() => {
  // 清理
});
</script>

<template>
  <div class="app">
    <Header
      :showSidebarToggle="showSidebarToggle"
      :sidebarCollapsed="sidebarCollapsed"
      version="v0.1.0"
      @toggle-sidebar="toggleSidebar"
    />

    <div class="main-content">
      <router-view v-slot="{ Component }">
        <component :is="Component" :sidebarCollapsed="sidebarCollapsed" />
      </router-view>
    </div>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
html,
body {
  height: 100%;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* 背景图片层 */
.app::before.app-background {
  content: "";
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-secondary);
  z-index: -1;
}

.main-content {
  flex: 1;
  overflow: hidden;
}
</style>
