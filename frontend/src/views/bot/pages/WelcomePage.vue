<script setup lang="ts">
import { computed } from "vue";
import { t } from "../../../locales";

const $t = computed(() => t);
</script>

<template>
  <div class="welcome-page">
    <div class="welcome-content">
      <h1>{{ $t("bot.welcome.title") || "欢迎使用 HAXAtom" }}</h1>
      <p>{{ $t("bot.welcome.subtitle") || "AI 智能体管理与多端分发平台" }}</p>
      <div class="feature-cards">
        <div class="feature-card">
          <div class="card-icon">🤖</div>
          <h3>模型管理</h3>
          <p>配置和管理多个 AI 模型提供商</p>
        </div>
        <div class="feature-card">
          <div class="card-icon">🎭</div>
          <h3>人格设定</h3>
          <p>创建和管理 AI 角色人设</p>
        </div>
        <div class="feature-card">
          <div class="card-icon">📚</div>
          <h3>知识库</h3>
          <p>构建私有知识库用于 RAG 检索</p>
        </div>
        <div class="feature-card">
          <div class="card-icon">⚡</div>
          <h3>预设方案</h3>
          <p>组合资源快速搭建 AI 智能体</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.welcome-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.welcome-content {
  text-align: center;
  max-width: 800px;
}

.welcome-content h1 {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.welcome-content p {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 40px;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.feature-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  transition: all 0.2s ease;
}

.feature-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: var(--primary-color);
}

.card-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.feature-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.feature-card p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}
</style>
