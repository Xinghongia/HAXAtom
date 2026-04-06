<template>
  <div class="markdown-body" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";

const props = defineProps<{
  content: string;
}>();

// 当前主题
const isDarkMode = ref(false);

// 检测主题
const checkTheme = () => {
  isDarkMode.value = document.documentElement.classList.contains("dark");
  loadHighlightTheme();
};

// 动态加载高亮主题
const loadHighlightTheme = () => {
  // 移除旧的主题样式
  const existingLink = document.getElementById("hljs-theme");
  if (existingLink) {
    existingLink.remove();
  }

  // 创建新的样式链接
  const link = document.createElement("link");
  link.id = "hljs-theme";
  link.rel = "stylesheet";
  link.href = isDarkMode.value
    ? "https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github-dark.css"
    : "https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github.css";
  document.head.appendChild(link);
};

// 监听主题变化
let observer: MutationObserver | null = null;

onMounted(() => {
  checkTheme();

  // 使用 MutationObserver 监听主题变化
  observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === "class") {
        checkTheme();
      }
    });
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class"],
  });
});

onUnmounted(() => {
  if (observer) {
    observer.disconnect();
  }
});

// 配置 markdown-it
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`;
      } catch (__) {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  },
});

const renderedContent = computed(() => {
  return md.render(props.content);
});
</script>

<style scoped>
.markdown-body {
  font-size: 16px;
  font-weight: 400;
  line-height: 1.8;
  color: var(--text-primary);
}

:deep(.markdown-body p) {
  margin-bottom: 20px;
}

:deep(.markdown-body p + p) {
  margin-top: 20px;
}

:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3),
:deep(.markdown-body h4),
:deep(.markdown-body h5),
:deep(.markdown-body h6) {
  margin-top: 24px;
  margin-bottom: 12px;
  font-weight: 700;
  line-height: 1.3;
  color: var(--text-primary);
}

/* 第一个标题不需要上边距 */
:deep(.markdown-body h1:first-child),
:deep(.markdown-body h2:first-child),
:deep(.markdown-body h3:first-child),
:deep(.markdown-body h4:first-child),
:deep(.markdown-body h5:first-child),
:deep(.markdown-body h6:first-child) {
  margin-top: 0;
}

/* 标题后面紧跟的段落或列表减少间距 */
:deep(.markdown-body h1 + p),
:deep(.markdown-body h2 + p),
:deep(.markdown-body h3 + p),
:deep(.markdown-body h4 + p),
:deep(.markdown-body h1 + ul),
:deep(.markdown-body h2 + ul),
:deep(.markdown-body h3 + ul),
:deep(.markdown-body h4 + ul),
:deep(.markdown-body h1 + ol),
:deep(.markdown-body h2 + ol),
:deep(.markdown-body h3 + ol),
:deep(.markdown-body h4 + ol) {
  margin-top: 8px;
}

:deep(.markdown-body h1) {
  font-size: 2.2em;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 0.3em;
}

:deep(.markdown-body h2) {
  font-size: 1.8em;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 0.3em;
}

:deep(.markdown-body h3) {
  font-size: 1.5em;
}

:deep(.markdown-body h4) {
  font-size: 1.25em;
}

:deep(.markdown-body ul),
:deep(.markdown-body ol) {
  margin-bottom: 16px;
}

:deep(.markdown-body ol) {
  counter-reset: item;
  list-style: none;
  padding-left: 2em;
}

:deep(.markdown-body ol li) {
  counter-increment: item;
  position: relative;
  padding-left: 1.5em;
  margin-bottom: 12px;
  line-height: 1.8;
}

:deep(.markdown-body ol li::before) {
  content: counter(item) ".";
  position: absolute;
  left: -1.5em;
  width: 1.5em;
  text-align: right;
  padding-right: 0.5em;
  font-weight: 700;
  color: var(--text-primary);
}

:deep(.markdown-body ul li) {
  position: relative;
  padding-left: 1.5em;
  margin-bottom: 12px;
  line-height: 1.8;
}

:deep(.markdown-body ul li::before) {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--text-secondary);
}

:deep(.markdown-body li > ul),
:deep(.markdown-body li > ol) {
  margin-top: 8px;
  margin-bottom: 0;
}

:deep(.markdown-body code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: var(--bg-tertiary);
  border-radius: 6px;
  font-family:
    ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono",
    monospace;
}

:deep(.markdown-body pre) {
  padding: 24px 28px !important;
  overflow: auto;
  font-size: 85%;
  line-height: 1.8;
  border-radius: 8px;
  margin: 20px 0 !important;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

:deep(.markdown-body pre code) {
  display: block;
  max-width: auto;
  padding: 0 0 0 16px !important;
  margin: 0;
  overflow: visible;
  line-height: inherit;
  word-wrap: normal;
  background-color: transparent !important;
  border: 0;
  border-radius: 0;
}

:deep(.markdown-body blockquote) {
  padding: 0 1em;
  color: var(--text-secondary);
  border-left: 0.25em solid var(--border-color);
  margin-bottom: 16px;
}

:deep(.markdown-body table) {
  display: block;
  width: 100%;
  overflow: auto;
  margin-bottom: 16px;
  border-spacing: 0;
  border-collapse: collapse;
}

:deep(.markdown-body table tr) {
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

:deep(.markdown-body table th),
:deep(.markdown-body table td) {
  padding: 6px 13px;
  border: 1px solid var(--border-color);
}

:deep(.markdown-body table tr:nth-child(2n)) {
  background-color: var(--bg-primary);
}

:deep(.markdown-body a) {
  color: var(--primary-color, #3b82f6);
  text-decoration: none;
}

:deep(.markdown-body a:hover) {
  text-decoration: underline;
}

:deep(.markdown-body hr) {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: var(--border-color);
  border: 0;
}

/* 代码块语言标签 */
:deep(.hljs) {
  position: relative;
}

:deep(.hljs::before) {
  content: attr(data-language);
  position: absolute;
  top: 0;
  right: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
}
</style>
