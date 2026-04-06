<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { t } from "../../../locales";
import CreatePersonalityModal from "../../../components/personality/CreatePersonalityModal.vue";
import {
  getPromptConfigList,
  getPromptConfigDetail,
  createPromptConfig,
  updatePromptConfig,
  deletePromptConfig,
  type PromptConfigListItem,
  type PromptConfig,
  type CreatePromptConfigRequest,
  type UpdatePromptConfigRequest,
} from "../../../api/promptConfig";

const $t = computed(() => t);

// 格式化日期
const formatDate = (dateStr?: string) => {
  if (!dateStr) return "未知时间";
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// 文件夹数据
const folders = ref([{ id: "root", name: "根目录", icon: "folder" }]);

const selectedFolder = ref("root");

// 提示词配置列表
const personalities = ref<PromptConfigListItem[]>([]);
const loading = ref(false);

// 创建弹窗显示状态
const showCreateModal = ref(false);

// 编辑模式状态
const isEditMode = ref(false);
const editingData = ref<PromptConfig | null>(null);

// 当前激活的菜单
const activeMenu = ref<string | null>(null);

// 切换菜单显示
const toggleMenu = (promptId: string) => {
  if (activeMenu.value === promptId) {
    activeMenu.value = null;
  } else {
    activeMenu.value = promptId;
  }
};

// 关闭菜单
const closeMenu = () => {
  activeMenu.value = null;
};

// 编辑人格
const handleEdit = async (personality: PromptConfigListItem) => {
  closeMenu();
  try {
    // 获取完整详情
    const detail = await getPromptConfigDetail(personality.prompt_id);
    editingData.value = detail;
    isEditMode.value = true;
    showCreateModal.value = true;
  } catch (error) {
    console.error("获取人格详情失败:", error);
    alert("获取人格详情失败，请重试");
  }
};

// 移动人格
const handleMove = (personality: PromptConfigListItem) => {
  console.log("移动人格:", personality);
  closeMenu();
  // TODO: 打开移动弹窗
};

// 加载提示词配置列表
const loadPromptConfigs = async () => {
  loading.value = true;
  try {
    const data = await getPromptConfigList();
    personalities.value = data;
  } catch (error) {
    console.error("加载提示词配置失败:", error);
  } finally {
    loading.value = false;
  }
};

// 创建人格
const handleCreatePersonality = async (data: CreatePromptConfigRequest) => {
  try {
    await createPromptConfig(data);
    showCreateModal.value = false;
    // 刷新列表
    await loadPromptConfigs();
  } catch (error) {
    console.error("创建人格失败:", error);
  }
};

// 更新人格
const handleUpdatePersonality = async (data: UpdatePromptConfigRequest) => {
  if (!editingData.value) return;
  try {
    await updatePromptConfig(editingData.value.prompt_id, data);
    showCreateModal.value = false;
    isEditMode.value = false;
    editingData.value = null;
    // 刷新列表
    await loadPromptConfigs();
    alert("更新成功");
  } catch (error) {
    console.error("更新人格失败:", error);
    alert("更新失败，请重试");
  }
};

// 删除人格
const handleDeletePersonality = async (promptId: string) => {
  closeMenu();
  if (!confirm("确定要删除这个人格吗？")) return;
  try {
    await deletePromptConfig(promptId);
    // 显示成功提示
    alert("删除成功");
    // 刷新列表
    await loadPromptConfigs();
  } catch (error) {
    console.error("删除人格失败:", error);
    alert("删除失败，请重试");
  }
};

onMounted(() => {
  loadPromptConfigs();
  // 点击外部关闭菜单
  document.addEventListener("click", closeMenu);
});

// 搜索关键词
const searchKeyword = ref("");

// 过滤后的人格列表
const filteredPersonalities = computed(() => {
  if (!searchKeyword.value) return personalities.value;
  const keyword = searchKeyword.value.toLowerCase();
  return personalities.value.filter(
    (p) =>
      p.prompt_name.toLowerCase().includes(keyword) ||
      (p.description?.toLowerCase() || "").includes(keyword),
  );
});

// 创建人格
const createPersonality = () => {
  isEditMode.value = false;
  editingData.value = null;
  showCreateModal.value = true;
};

// 新建文件夹
const createFolder = () => {
  console.log("新建文件夹");
};
</script>

<template>
  <div class="personality-view">
    <!-- 头部 -->
    <div class="personality-header">
      <div class="header-title">
        <svg class="title-icon" viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
          />
        </svg>
        <div class="title-text">
          <h1>{{ $t("personality.title") || "人格设定" }}</h1>
          <p>{{ $t("personality.subtitle") || "管理人格角色设定" }}</p>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="personality-content">
      <!-- 左侧文件夹树 -->
      <div class="folder-sidebar">
        <div class="folder-header">
          <span class="folder-title">{{
            $t("personality.folders") || "文件夹"
          }}</span>
          <button class="folder-add-btn" @click="createFolder">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M14 10H2v2h12v-2zm0-4H2v2h12V6zm4 8v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zM2 16h8v-2H2v2z"
              />
            </svg>
          </button>
        </div>

        <!-- 搜索框 -->
        <div class="folder-search">
          <svg class="search-icon" viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"
            />
          </svg>
          <input
            v-model="searchKeyword"
            type="text"
            :placeholder="$t('personality.searchFolder') || '搜索文件夹...'"
          />
        </div>

        <!-- 文件夹列表 -->
        <div class="folder-list">
          <div
            v-for="folder in folders"
            :key="folder.id"
            class="folder-item"
            :class="{ active: selectedFolder === folder.id }"
            @click="selectedFolder = folder.id"
          >
            <svg class="folder-icon" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"
              />
            </svg>
            <span class="folder-name">{{ folder.name }}</span>
          </div>

          <!-- 空状态 -->
          <div class="folder-empty">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z"
              />
            </svg>
            <span>{{ $t("personality.noFolders") || "暂无文件夹" }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧人格列表 -->
      <div class="personality-main">
        <!-- 工具栏 -->
        <div class="toolbar">
          <div class="breadcrumb">
            <svg
              class="breadcrumb-icon"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path
                d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"
              />
            </svg>
            <span class="breadcrumb-text">{{
              $t("personality.rootFolder") || "根目录"
            }}</span>
            <span class="breadcrumb-count"
              >({{ filteredPersonalities.length }})</span
            >
          </div>
          <div class="toolbar-actions">
            <button class="btn btn-primary" @click="createPersonality">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
              </svg>
              {{ $t("personality.create") || "创建人格" }}
            </button>
            <button class="btn btn-secondary" @click="createFolder">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path
                  d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z"
                />
              </svg>
              {{ $t("personality.newFolder") || "新建文件夹" }}
            </button>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <span>加载中...</span>
        </div>

        <!-- 空状态 -->
        <div v-else-if="filteredPersonalities.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"
            />
          </svg>
          <span>暂无数据，点击"创建人格"添加</span>
        </div>

        <!-- 人格卡片网格 -->
        <div v-else class="personality-grid">
          <div
            v-for="personality in filteredPersonalities"
            :key="personality.prompt_id"
            class="personality-card"
          >
            <div class="card-header">
              <h3 class="card-title">{{ personality.prompt_name }}</h3>
              <div class="card-menu-wrapper">
                <button
                  class="card-more-btn"
                  @click.stop="toggleMenu(personality.prompt_id)"
                  title="更多操作"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path
                      d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"
                    />
                  </svg>
                </button>
                <!-- 下拉菜单 -->
                <div
                  v-if="activeMenu === personality.prompt_id"
                  class="dropdown-menu"
                >
                  <div class="menu-item" @click="handleEdit(personality)">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path
                        d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"
                      />
                    </svg>
                    <span>编辑</span>
                  </div>
                  <div class="menu-item" @click="handleMove(personality)">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path
                        d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 9h-4v2h4v2l3-3-3-3v2z"
                      />
                    </svg>
                    <span>移动到...</span>
                  </div>
                  <div class="menu-divider"></div>
                  <div
                    class="menu-item delete"
                    @click="handleDeletePersonality(personality.prompt_id)"
                  >
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path
                        d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"
                      />
                    </svg>
                    <span>删除</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="card-body">
              <p class="card-description">
                {{ personality.system_prompt }}
              </p>

              <!-- 创建时间 -->
              <div class="card-special-tags">
                <span class="special-tag time-tag">
                  {{ formatDate(personality.created_at) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑人格弹窗 -->
    <CreatePersonalityModal
      v-model="showCreateModal"
      :is-edit="isEditMode"
      :edit-data="editingData"
      @submit="handleCreatePersonality"
      @update="handleUpdatePersonality"
    />
  </div>
</template>

<style scoped>
.personality-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

/* 头部 */
.personality-header {
  padding: 24px 32px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  width: 32px;
  height: 32px;
  color: var(--text-primary);
}

.title-text h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.title-text p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 4px 0 0 0;
}

/* 主内容区 */
.personality-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧文件夹侧边栏 */
.folder-sidebar {
  width: 260px;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

/* 深色模式 */
html.dark .folder-sidebar {
  background: #1a1a1a;
}

.folder-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
}

.folder-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.folder-add-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.folder-add-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.folder-add-btn svg {
  width: 18px;
  height: 18px;
}

/* 文件夹搜索 */
.folder-search {
  position: relative;
  padding: 12px 16px;
}

.folder-search .search-icon {
  position: absolute;
  left: 24px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
}

.folder-search input {
  width: 100%;
  padding: 8px 12px 8px 36px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  background: var(--bg-primary);
  color: var(--text-primary);
  outline: none;
  transition: all 0.2s;
}

.folder-search input:focus {
  border-color: var(--primary-color);
}

.folder-search input::placeholder {
  color: var(--text-tertiary);
}

/* 文件夹列表 */
.folder-list {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
}

.folder-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 2px;
}

.folder-item:hover {
  background: var(--bg-hover);
}

.folder-item.active {
  background: var(--primary-light);
}

.folder-item.active .folder-name {
  color: var(--primary-color);
  font-weight: 500;
}

.folder-icon {
  width: 18px;
  height: 18px;
  color: var(--text-secondary);
}

.folder-item.active .folder-icon {
  color: var(--primary-color);
}

.folder-name {
  font-size: 13px;
  color: var(--text-primary);
}

/* 空文件夹状态 */
.folder-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-tertiary);
}

.folder-empty svg {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.folder-empty span {
  font-size: 13px;
}

/* 右侧主内容区 */
.personality-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
}

.breadcrumb-icon {
  width: 18px;
  height: 18px;
  color: var(--text-secondary);
}

.breadcrumb-text {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.breadcrumb-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.toolbar-actions {
  display: flex;
  gap: 12px;
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
  background: rgb(236, 245, 255);
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
}

.btn-primary:hover {
  background: rgb(220, 238, 255);
  color: var(--primary-color);
}

/* 深色模式按钮 */
html.dark .btn-primary {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border-color: #3b82f6;
}

html.dark .btn-primary:hover {
  background: rgba(59, 130, 246, 0.25);
  color: #60a5fa;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-hover);
}

/* 人格卡片网格 */
.personality-grid {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  align-content: start;
}

/* 人格卡片 */
.personality-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
  cursor: pointer;
}

.personality-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: var(--primary-color);
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.4;
  flex: 1;
  padding-right: 8px;
}

.card-more-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.card-more-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.card-more-btn svg {
  width: 18px;
  height: 18px;
}

/* 下拉菜单 */
.card-menu-wrapper {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  min-width: 140px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  padding: 4px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  color: var(--text-primary);
}

.menu-item:hover {
  background: var(--bg-hover);
}

.menu-item svg {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

.menu-item.delete {
  color: #ff4d4f;
}

.menu-item.delete svg {
  color: #ff4d4f;
}

.menu-divider {
  height: 1px;
  background: var(--border-color);
  margin: 4px 0;
}

.card-body {
  flex: 1;
}

.card-description {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 特殊标签 */
.card-special-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.special-tag {
  font-size: 11px;
  padding: 4px 10px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  border: 1px solid #91d5ff;
}

.special-tag.inactive {
  background: #f5f5f5;
  color: #999;
  border-color: #d9d9d9;
}

.special-tag.time-tag {
  background: #f6ffed;
  color: #52c41a;
  border-color: #b7eb8f;
}

/* 深色模式时间标签 */
html.dark .special-tag.time-tag {
  background: rgba(82, 196, 26, 0.15);
  color: #73d13d;
  border-color: rgba(82, 196, 26, 0.3);
}

/* 工具数量 */
.card-tools {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.card-tools svg {
  width: 14px;
  height: 14px;
  color: var(--text-tertiary);
}

.card-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.card-id {
  font-size: 11px;
  color: var(--text-tertiary);
  font-family: monospace;
}

/* 加载状态 */
.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 空状态 */
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
