<script setup lang="ts">
import { ref, watch } from "vue";
import Sidebar from "../../components/Sidebar.vue";
import ModelProviderView from "./ModelProviderView.vue";
import GeneralConfig from "../../components/config/GeneralConfig.vue";
import PersonalityView from "./PersonalityView.vue";

// 接收从父组件传递下来的侧边栏状态
const props = withDefaults(
  defineProps<{
    sidebarCollapsed?: boolean;
  }>(),
  {
    sidebarCollapsed: false,
  },
);

// 当前页面
const currentPage = ref("welcome");

// 切换页面
const changePage = (page: string) => {
  currentPage.value = page;
};

// 监听侧边栏状态变化（可选，用于调试）
watch(
  () => props.sidebarCollapsed,
  (newVal) => {
    console.log("BotView: 侧边栏状态变化", newVal ? "已折叠" : "已展开");
  },
);
</script>

<template>
  <div class="bot-page">
    <Sidebar
      :collapsed="props.sidebarCollapsed"
      :active-page="currentPage"
      @change-page="changePage"
    />
    <div class="main-area">
      <!-- 欢迎页面 -->
      <div v-if="currentPage === 'welcome'" class="welcome-content">
        <h1>欢迎使用 HAXAtom</h1>
        <p>请从左侧菜单选择功能</p>
      </div>

      <!-- 机器人页面 -->
      <div v-else-if="currentPage === 'bot'" class="bot-content">
        <h1>机器人配置</h1>
        <p>机器人配置功能开发中...</p>
      </div>

      <!-- 模型提供商页面 -->
      <ModelProviderView v-else-if="currentPage === 'model'" />

      <!-- 普通配置页面 -->
      <GeneralConfig v-else-if="currentPage === 'generalConfig'" />

      <!-- 人格设定页面 -->
      <PersonalityView v-else-if="currentPage === 'personality'" />

      <!-- 其他页面 -->
      <div v-else class="placeholder-content">
        <h1>功能开发中</h1>
        <p>该功能正在开发中，敬请期待...</p>
      </div>
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

.welcome-content,
.bot-content,
.placeholder-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
}

.welcome-content h1,
.bot-content h1,
.placeholder-content h1 {
  font-size: 28px;
  margin-bottom: 16px;
}

.welcome-content p,
.bot-content p,
.placeholder-content p {
  font-size: 16px;
  color: var(--text-secondary);
}
</style>
