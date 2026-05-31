<script setup>
import { provide } from "vue";
import { useLearning } from "./composables/useLearning";
import SideNav from "./components/SideNav.vue";
import DebugPanel from "./components/DebugPanel.vue";

const learning = useLearning();

// 将学习状态提供给所有子组件
provide("learning", learning);

const {
  appState,
  currentWordIndex,
  totalLearningCount,
  handleNext,
  debugMode,
  debugWordInfo,
} = learning;
</script>

<template>
  <!-- 侧边导航 -->
  <SideNav />

  <!-- 页面内容 -->
  <main class="app-main">
    <router-view />
  </main>

  <!-- Debug 面板 -->
  <DebugPanel v-if="debugMode" :debug-word-info="debugWordInfo" />

  <!-- 详情页的浮动"下一个"按钮 -->
  <Teleport to="body">
    <button v-if="appState === 'detail'" class="next-btn-fixed" @click="handleNext">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="9 18 15 12 9 6"></polyline>
      </svg>
      {{ currentWordIndex + 1 >= totalLearningCount ? "完成" : "下一个" }}
      <kbd>Enter</kbd>
    </button>
  </Teleport>
</template>

<style>
@import "./style.css";

/* 浮动下一个按钮 */
.next-btn-fixed {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 1000;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(90deg, #4f46e5, #7c3aed);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 4px 20px rgba(79, 70, 229, 0.4);
}

.next-btn-fixed:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(79, 70, 229, 0.5);
}

.next-btn-fixed kbd {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  padding: 0.1rem 0.4rem;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
}
</style>
