<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import Sidebar from "../../components/Sidebar.vue";

// 接收从父组件传递下来的侧边栏状态
const props = withDefaults(
  defineProps<{
    sidebarCollapsed?: boolean;
  }>(),
  {
    sidebarCollapsed: false,
  },
);

const route = useRoute();

// 当前激活的路由名称
const activeRoute = computed(() => route.name as string);
</script>

<template>
  <div class="bot-page">
    <Sidebar :collapsed="props.sidebarCollapsed" :active-route="activeRoute" />
    <div class="main-area">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.bot-page {
  height: 100%;
  display: flex;
  background: #f9fafb;
  transition: background-color 0.3s ease;
}

html.dark .bot-page {
  background: #1a1a1a;
}

.main-area {
  flex: 1;
  overflow-y: auto;
}
</style>
