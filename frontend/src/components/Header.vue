<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  currentLanguage,
  isDarkMode,
  toggleDarkMode,
  bgOpacity,
  setBgOpacity,
} from "../stores/settings";
import { t } from "../locales";

const props = withDefaults(
  defineProps<{
    version?: string;
    showSidebarToggle?: boolean;
    sidebarCollapsed?: boolean;
  }>(),
  {
    version: "v0.1.0",
    showSidebarToggle: false,
    sidebarCollapsed: false,
  },
);

const emit = defineEmits<{
  toggleSidebar: [];
}>();

const route = useRoute();
const router = useRouter();

const showSettingsMenu = ref(false);
const showLanguageSubmenu = ref(false);
const settingsWrapper = ref<HTMLElement | null>(null);
const showOpacitySlider = ref(false);

// 翻译函数
const $t = computed(() => t);

// 当前激活的路由名称
const currentRouteName = computed(() => {
  const name = route.name as string;
  // 如果是 ChatWithSession 路由，也认为是 Chat 页面
  if (name === "ChatWithSession") {
    return "Chat";
  }
  return name;
});

// 切换路由
const switchTab = (tabName: string) => {
  router.push({ name: tabName });
};

// 切换侧边栏
const toggleSidebar = () => {
  emit("toggleSidebar");
};

// 处理透明度变化
const handleOpacityChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  setBgOpacity(Number(target.value));
};

// 切换暗黑模式
const handleToggleDarkMode = () => {
  toggleDarkMode();
};

// 选择语言
const selectLanguage = (lang: string) => {
  currentLanguage.value = lang;
  showLanguageSubmenu.value = false;
  // 只关闭二级菜单，不关闭设置菜单
};
</script>

<template>
  <header class="header">
    <div class="header-left">
      <!-- 侧边栏折叠按钮 - 只在 Bot 页面显示 -->
      <button
        v-if="showSidebarToggle"
        class="sidebar-toggle-btn"
        @click="toggleSidebar"
        title="收起/展开侧边栏"
      >
        <svg
          class="icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M3 12h18M3 6h18M3 18h18" v-if="!sidebarCollapsed" />
          <path d="M3 6h18M3 12h18M3 18h18" v-else />
        </svg>
      </button>

      <div class="logo">
        <svg
          class="logo-icon"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#409EFF" />
          <path
            d="M2 17L12 22L22 17"
            stroke="#409EFF"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M2 12L12 17L22 12"
            stroke="#409EFF"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <span class="logo-text">HAXAtom</span>
        <span class="version">{{ version }}</span>
      </div>
    </div>
    <div class="header-right">
      <nav class="nav-tabs">
        <button
          class="nav-tab"
          :class="{ active: currentRouteName === 'Bot' }"
          @click="switchTab('Bot')"
        >
          <svg
            class="tab-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="9" cy="9" r="2" />
            <path d="M15 8h2M15 12h2M15 16h2" />
          </svg>
          <span>{{ $t("nav.bot") }}</span>
        </button>
        <button
          class="nav-tab"
          :class="{ active: currentRouteName === 'Chat' }"
          @click="switchTab('Chat')"
        >
          <svg
            class="tab-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
            />
          </svg>
          <span>{{ $t("nav.chat") }}</span>
        </button>
      </nav>

      <div
        ref="settingsWrapper"
        class="settings-wrapper"
        @mouseenter="showSettingsMenu = true"
        @mouseleave="showSettingsMenu = false"
      >
        <button class="settings-btn" title="设置">
          <svg
            class="icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="3" />
            <path
              d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
            />
          </svg>
        </button>

        <!-- 设置菜单 -->
        <div v-if="showSettingsMenu" class="settings-menu">
          <!-- 语言选择 -->
          <div
            class="menu-item has-submenu"
            @mouseenter="showLanguageSubmenu = true"
            @mouseleave="showLanguageSubmenu = false"
          >
            <div class="menu-item-left">
              <svg
                class="menu-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2a14.5 14.5 0 0 0 0 20M2 12h20" />
              </svg>
              <span>{{ $t("settings.language") }}</span>
            </div>
            <div class="menu-item-right">
              <span class="current-value">{{
                currentLanguage === "zh-CN"
                  ? "CN"
                  : currentLanguage.toUpperCase()
              }}</span>
              <svg
                class="arrow-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M9 18l6-6-6-6" />
              </svg>
            </div>
            <div
              class="submenu"
              :class="{ show: showLanguageSubmenu }"
              @mouseenter="showLanguageSubmenu = true"
              @mouseleave="showLanguageSubmenu = false"
            >
              <div
                class="submenu-item"
                :class="{ active: currentLanguage === 'zh-CN' }"
                @click.stop="selectLanguage('zh-CN')"
              >
                <span class="submenu-prefix">CN</span>
                {{ $t("language.cn") }}
              </div>
              <div
                class="submenu-item"
                :class="{ active: currentLanguage === 'en' }"
                @click.stop="selectLanguage('en')"
              >
                <span class="submenu-prefix">US</span>
                {{ $t("language.en") }}
              </div>
              <div
                class="submenu-item"
                :class="{ active: currentLanguage === 'zh-TW' }"
                @click.stop="selectLanguage('zh-TW')"
              >
                <span class="submenu-prefix">TW</span>
                {{ $t("language.tw") }}
              </div>
              <div
                class="submenu-item"
                :class="{ active: currentLanguage === 'ja' }"
                @click.stop="selectLanguage('ja')"
              >
                <span class="submenu-prefix">JP</span>
                {{ $t("language.ja") }}
              </div>
              <div
                class="submenu-item"
                :class="{ active: currentLanguage === 'ko' }"
                @click.stop="selectLanguage('ko')"
              >
                <span class="submenu-prefix">KR</span>
                {{ $t("language.ko") }}
              </div>
              <div
                class="submenu-item"
                :class="{ active: currentLanguage === 'ru' }"
                @click.stop="selectLanguage('ru')"
              >
                <span class="submenu-prefix">RU</span>
                {{ $t("language.ru") }}
              </div>
            </div>
          </div>

          <!-- 深色模式 -->
          <div class="menu-item" @click="handleToggleDarkMode">
            <div class="menu-item-left">
              <svg
                v-if="isDarkMode"
                class="menu-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <circle cx="12" cy="12" r="5" />
                <path
                  d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
                />
              </svg>
              <svg
                v-else
                class="menu-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
              <span>{{
                isDarkMode ? $t("settings.lightMode") : $t("settings.darkMode")
              }}</span>
            </div>
          </div>

          <!-- 更新 -->
          <div class="menu-item">
            <div class="menu-item-left">
              <svg
                class="menu-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M12 19V5M5 12l7-7 7 7" />
              </svg>
              <span>{{ $t("settings.update") }}</span>
            </div>
          </div>

          <!-- 账户 -->
          <div class="menu-item">
            <div class="menu-item-left">
              <svg
                class="menu-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
              <span>{{ $t("settings.account") }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  height: 56px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  transition: background-color 0.3s ease;
}

html.dark .header {
  background: var(--bg-primary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar-toggle-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: var(--text-secondary);
}

.sidebar-toggle-btn:hover {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.sidebar-toggle-btn .icon {
  width: 20px;
  height: 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 28px;
  height: 28px;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.version {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: 8px;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.nav-tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-tab.active {
  color: var(--primary-color);
  background: rgba(64, 158, 255, 0.1);
}

.tab-icon {
  width: 16px;
  height: 16px;
}

.settings-wrapper {
  position: relative;
}

.settings-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: var(--text-secondary);
}

.settings-btn:hover {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.settings-btn .icon {
  width: 20px;
  height: 20px;
}

.settings-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 8px;
  min-width: 240px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

.settings-menu::before {
  content: "";
  position: absolute;
  top: -12px;
  left: 0;
  width: 100%;
  height: 12px;
  background: transparent;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  color: var(--text-primary);
  font-size: 14px;
  position: relative;
  gap: 12px;
}

.menu-item:hover {
  background: rgba(64, 158, 255, 0.1);
}

.menu-item-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.menu-item-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-icon {
  width: 20px;
  height: 20px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.arrow-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

.menu-item.has-submenu .submenu.show {
  display: block;
}

.current-value {
  color: var(--text-secondary);
  font-size: 13px;
}

.opacity-slider-small {
  width: 60px;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--border-color);
  border-radius: 2px;
  outline: none;
}

.opacity-slider-small::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 12px;
  height: 12px;
  background: var(--primary-color);
  border-radius: 50%;
  cursor: pointer;
}

.opacity-slider-small::-moz-range-thumb {
  width: 12px;
  height: 12px;
  background: var(--primary-color);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.opacity-value-small {
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 32px;
  text-align: right;
}

.submenu {
  display: none;
  position: absolute;
  left: 0;
  top: -30px;
  transform: translateX(calc(-100% - 12px));
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 8px;
  min-width: 180px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 101;
}

.submenu::before {
  content: "";
  position: absolute;
  right: -12px;
  top: 10px;
  width: 12px;
  height: calc(100% - 10px);
  background: transparent;
}

.submenu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 13px;
  color: var(--text-primary);
}

.submenu-item:hover,
.submenu-item.active {
  background: var(--bg-hover);
}

.submenu-item.active {
  background: rgba(64, 158, 255, 0.1);
}

.submenu-prefix {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 600;
  min-width: 24px;
}

@keyframes vuetify-ripple {
  to {
    transform: scale(1);
    opacity: 0;
  }
}
</style>
