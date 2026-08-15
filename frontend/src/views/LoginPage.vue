<script setup>
import { ref, onUnmounted } from "vue";
import { apiService } from "../utils/api";

const status = ref("idle"); // idle | starting | waiting | success | error
const message = ref("");
const taskId = ref("");
let pollTimer = null;

async function startLogin() {
  status.value = "starting";
  message.value = "正在启动浏览器…";
  try {
    const resp = await apiService.startLogin();
    taskId.value = resp.task_id;
    status.value = "waiting";
    message.value = "已打开浏览器，请在弹出的窗口中完成扇贝登录（微信扫码 / 账号登录均可）";
    pollTimer = setInterval(pollStatus, 2000);
  } catch (err) {
    status.value = "error";
    const detail = err?.response?.data?.detail || err?.message || err;
    message.value = `无法连接后端（${detail}）。请确认后端已启动，并已重启加载新代码。`;
  }
}

async function pollStatus() {
  if (!taskId.value) return;
  try {
    const resp = await apiService.getLoginStatus(taskId.value);
    status.value = resp.status;
    message.value = resp.message;

    if (resp.status === "success" || resp.status === "error") {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  } catch (err) {
    // 任务可能因后端重启丢失，停止轮询并提示
    clearInterval(pollTimer);
    pollTimer = null;
    status.value = "error";
    message.value = `查询登录状态失败: ${err?.message || err}`;
  }
}

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-icon">🔑</div>
      <h1 class="login-title">外置登录</h1>
      <p class="login-desc">
        点击下方按钮后，会打开一个真实浏览器窗口。<br />
        你只需要像平时一样登录扇贝，应用会自动抓取并保存 Cookie，以后不用再按 F12。
      </p>

      <button class="login-btn" :disabled="status === 'starting' || status === 'waiting'" @click="startLogin">
        {{ status === "waiting" ? "等待登录中…" : "开始外置登录" }}
      </button>
      <div v-if="message" class="login-message" :class="status">
        {{ message }}
      </div>

      <div v-if="status === 'waiting'" class="login-tip">
        💡 如果已经登录过，浏览器可能会直接自动登录，无需任何操作。
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.login-card {
  max-width: 520px;
  width: 100%;
  background: rgba(15, 18, 30, 0.7);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 20px;
  padding: 2.5rem;
  text-align: center;
  backdrop-filter: blur(12px);
}

.login-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.login-title {
  font-size: 1.8rem;
  font-weight: 800;
  color: #e0e7ff;
  margin: 0 0 0.75rem;
}

.login-desc {
  color: #9ca3af;
  line-height: 1.7;
  margin-bottom: 1.75rem;
}

.login-btn {
  padding: 0.85rem 2.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.4);
  background: linear-gradient(90deg, #4f46e5, #7c3aed);
  color: white;
  cursor: pointer;
  transition: all 0.25s ease;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(79, 70, 229, 0.4);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-message {
  margin-top: 1.25rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: rgba(99, 102, 241, 0.08);
  color: #c7d2fe;
  font-size: 0.9rem;
  word-break: break-all;
}

.login-message.success {
  background: rgba(16, 185, 129, 0.12);
  color: #6ee7b7;
}

.login-message.error {
  background: rgba(239, 68, 68, 0.12);
  color: #fca5a5;
}

.login-tip {
  margin-top: 1rem;
  color: #6b7280;
  font-size: 0.85rem;
}
</style>
