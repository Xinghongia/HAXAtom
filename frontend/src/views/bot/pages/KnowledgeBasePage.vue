<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { t } from "../../../locales";

const $t = computed(() => t);

const loading = ref(false);
const knowledgeBases = ref([]);

const loadKnowledgeBases = async () => {
  loading.value = true;
  try {
    // TODO: 调用 API 获取知识库列表
    console.log("加载知识库列表");
  } catch (error) {
    console.error("加载知识库失败:", error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadKnowledgeBases();
});
</script>

<template>
  <div class="knowledge-base-page">
    <div class="page-header">
      <h1>{{ $t("bot.knowledge.title") || "知识库管理" }}</h1>
      <p>{{ $t("bot.knowledge.subtitle") || "管理 RAG 知识库资源" }}</p>
    </div>

    <div class="page-content">
      <div class="toolbar">
        <button class="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
          </svg>
          {{ $t("bot.knowledge.create") || "创建知识库" }}
        </button>
      </div>

      <div v-if="loading" class="loading-state">
        <span>加载中...</span>
      </div>

      <div v-else-if="knowledgeBases.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
        </svg>
        <span>暂无知识库，点击"创建知识库"添加</span>
      </div>

      <div v-else class="knowledge-base-list">
        <!-- 知识库列表 -->
      </div>
    </div>
  </div>
</template>

<style scoped>
.knowledge-base-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px 32px;
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
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn svg {
  width: 16px;
  height: 16px;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
}

.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  gap: 12px;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  opacity: 0.5;
}

.empty-state span {
  font-size: 14px;
}
</style>
