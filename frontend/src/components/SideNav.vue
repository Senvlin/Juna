<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { apiService } from "../utils/api";
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();
const isOpen = ref(false);
const showHamburger = ref(true);
const hamburgerEnter = ref(false);
const particles = ref([]);
let particleId = 0;
const userStatus = ref({ logged_in: false, username: null });
const avatarText = computed(() => {
  const name = userStatus.value.username;
  return name ? name.charAt(0).toUpperCase() : "?";
});

const navItems = [
    { label: "\u9996\u9875", icon: "\ud83c\udfe0", route: "welcome" },
    { label: "\u5b66\u4e60", icon: "\ud83d\udcd6", route: "learn" },

];

function isActive(name) {
    return route.name === name;
}


async function loadUserStatus() {
  try {
    const data = await apiService.getUserStatus();
    userStatus.value = data;
  } catch (err) {
    console.error("获取用户状态失败:", err);
    userStatus.value = { logged_in: false, username: null };
  }
}

function goLogin() {
  close();
  router.push({ name: "login" });
}
function goTo(name) {
    close();
    router.push({ name });
}

function toggle() {
    if (!isOpen.value) {
        isOpen.value = true;
        showHamburger.value = false;
    } else {
        close();
    }
}

function close() {
    isOpen.value = false;
    hamburgerEnter.value = true;
    showHamburger.value = true;
    setTimeout(() => {
        hamburgerEnter.value = false;
    }, 500);
}

function handleOpenNav(e) {
    if (e.key === 'e') {
        toggle();
    }
}

onMounted(() => {
    window.addEventListener("keydown", handleOpenNav);
    loadUserStatus();
});
watch(() => route.fullPath, loadUserStatus);
onUnmounted(() => {
    window.removeEventListener("keydown", handleOpenNav);
});
</script>

<template>

    <button v-if="showHamburger" class="hamburger" :class="{ entering: hamburgerEnter }" @click="toggle" aria-label="Menu">
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
    </button>

    <div v-if="isOpen" class="overlay" @click="close"></div>

    <div class="sidebar" :class="{ open: isOpen }">
        <div class="sidebar-header">
            <span class="sidebar-logo">📚</span>
            <span class="sidebar-title">单词学习</span>
            <button class="close-btn" @click="close" aria-label="Close">✕</button>
        </div>
        <nav class="sidebar-nav">
            <button v-for="item in navItems" :key="item.route" class="sidebar-item" :class="{ active: isActive(item.route) }" @click="goTo(item.route)">
                <span class="sidebar-item-icon">{{ item.icon }}</span>
                <span class="sidebar-item-label">{{ item.label }}</span>
            </button>
        </nav>
          <div class="sidebar-footer" @click="goLogin">
              <div class="user-avatar" :class="{ offline: !userStatus.logged_in }">
                  {{ avatarText }}
              </div>
              <span class="user-name" :class="{ offline: !userStatus.logged_in }">
                  {{ userStatus.logged_in ? userStatus.username : "未登录" }}
              </span>
          </div>
    </div>
</template>

<style scoped>
.hamburger {
    position: fixed;
    top: 20px;
    left: 20px;
    z-index: 200;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 1px solid rgba(99, 102, 241, 0.2);
    background: rgba(10, 12, 21, 0.6);
    backdrop-filter: blur(8px);
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3.5px;
    transition: opacity 0.15s ease, transform 0.15s ease;
}

.hamburger:hover {
    border-color: rgba(99, 102, 241, 0.4);
}

.hamburger.entering {
    animation: slideInLeft 0.45s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

@keyframes slideInLeft {
    0% {
        opacity: 0;
        transform: translateX(-60px) scale(0.6);
    }

    100% {
        opacity: 1;
        transform: translateX(0) scale(1);
    }
}

.hamburger-line {
    display: block;
    width: 17px;
    height: 2px;
    background: #9ca3af;
    border-radius: 2px;
    transition: all 0.25s ease;
}

@keyframes burst {
    0% {
        opacity: 1;
        transform: translate(0, 0) scale(1);
    }

    100% {
        opacity: 0;
        transform: translate(var(--x), var(--y)) scale(0.2);
    }
}

.overlay {
    position: fixed;
    inset: 0;
    z-index: 150;
    background: rgba(0, 0, 0, 0.5);
    animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}

.sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 180;
    width: 260px;
    background: rgba(10, 12, 21, 0.95);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(99, 102, 241, 0.12);
    padding: 1.5rem;
    transform: translateX(-100%);
    transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
    display: flex;
    flex-direction: column;
}

.sidebar.open {
    transform: translateX(0);
}

.sidebar-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(99, 102, 241, 0.1);
}

.sidebar-logo {
    font-size: 1.3rem;
}

.sidebar-title {
    font-size: 1rem;
    font-weight: 700;
    background: linear-gradient(135deg, #e0e7ff, #818cf8);
    background-clip: text;
    -webkit-background-clip: text;
    color: transparent;
    flex: 1;
}

.close-btn {
    background: transparent;
    border: none;
    color: #6b7280;
    font-size: 1.1rem;
    cursor: pointer;
    padding: 4px;
    transition: color 0.2s;
    line-height: 1;
}

.close-btn:hover {
    color: #e0e7ff;
}

.sidebar-nav {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.sidebar-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.7rem 1rem;
    background: transparent;
    border: none;
    border-radius: 10px;
    color: #9ca3af;
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
    width: 100%;
}

.sidebar-item:hover {
    color: #e0e7ff;
    background: rgba(99, 102, 241, 0.08);
}

.sidebar-item.active {
    color: #818cf8;
    background: rgba(99, 102, 241, 0.12);
}

.sidebar-item-icon {
    font-size: 1.1rem;
}

.sidebar-footer {
    margin-top: auto;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.85rem 1rem;
    border-top: 1px solid rgba(99, 102, 241, 0.1);
    cursor: pointer;
    border-radius: 10px;
    transition: background 0.2s ease;
}

.sidebar-footer:hover {
    background: rgba(99, 102, 241, 0.08);
}

.user-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1rem;
    color: white;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    flex-shrink: 0;
    user-select: none;
}

.user-avatar.offline {
    background: #374151;
    color: #9ca3af;
}

.user-name {
    color: #e0e7ff;
    font-size: 0.9rem;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.user-name.offline {
    color: #6b7280;
}
</style>
