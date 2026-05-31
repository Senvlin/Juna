<script setup>
import { ref, onMounted, inject } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const { startLearning } = inject("learning");

const displayText = ref("");
const fullText = "Juna";
const showCursor = ref(true);

let index = 0;
let deleting = false;
let timer;

function nextChar() {
    if (!deleting) {
        if (index < fullText.length) {
            displayText.value += fullText[index];
            index++;
            timer = setTimeout(nextChar, 120);
        } else {
            deleting = true;
            timer = setTimeout(nextChar, 1500);
        }
    } else {
        if (index > 0) {
            displayText.value = displayText.value.slice(0, -1);
            index--;
            timer = setTimeout(nextChar, 60);
        } else {
            deleting = false;
            timer = setTimeout(nextChar, 400);
        }
    }
}

onMounted(() => {
    timer = setTimeout(nextChar, 500);
    setInterval(() => {
        showCursor.value = !showCursor.value;
    }, 530);
});

function goLearn() {
    startLearning();
    router.push({ name: "learn" });
}
</script>

<template>
    <div class="welcome-page">
        <div class="hero">
            <h1 class="title">
                {{ displayText }}<span class="cursor" :class="{ blink: !showCursor }">|</span>
            </h1>
        </div>
        <div class="actions">
            <button class="btn" @click="goLearn">单词学习</button>
            <button class="btn disabled" disabled>阅读训练</button>
        </div>
        <div class="footer-info">
            <span class="today-label">今日待学习 · 开启新的一天</span>
        </div>
    </div>
</template>

<style scoped>
.welcome-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 2rem;
    position: relative;
    margin-top: -10vh;
}

.hero {
    text-align: center;
}

.title {
    font-size: 6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #e0e7ff 0%, #818cf8 40%, #c084fc 70%, #f472b6 100%);
    background-clip: text;
    -webkit-background-clip: text;
    color: transparent;
    letter-spacing: 0.05em;
    user-select: none;
}

.cursor {
    background: linear-gradient(135deg, #818cf8, #c084fc);
    background-clip: text;
    -webkit-background-clip: text;
    color: transparent;
    font-weight: 800;
}

.cursor.blink {
    visibility: hidden;
}

.actions {
    display: flex;
    gap: 1.5rem;
    margin-top: 2.5rem;
}

.btn {
    padding: 0.85rem 2.8rem;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 12px;
    border: 1px solid rgba(99, 102, 241, 0.3);
    background: rgba(15, 18, 30, 0.5);
    color: #cbd5e1;
    cursor: pointer;
    transition: all 0.25s ease;
    letter-spacing: 0.03em;
    min-width: 150px;
    backdrop-filter: blur(8px);
    position: relative;
    overflow: hidden;
}

.btn::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(192, 132, 252, 0.05));
    opacity: 0;
    transition: opacity 0.25s ease;
}

.btn:hover:not(.disabled)::before {
    opacity: 1;
}

.btn:hover:not(.disabled) {
    border-color: #818cf8;
    color: #e0e7ff;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.15), inset 0 0 20px rgba(99, 102, 241, 0.05);
    transform: translateY(-1px);
}

.btn.disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

.footer-info {
    position: absolute;
    bottom: 2.5rem;
    text-align: center;
}

.today-label {
    font-size: 0.85rem;
    color: #6b7280;
    letter-spacing: 0.04em;
}

@media (max-width: 640px) {
    .title {
        font-size: 3.5rem;
    }

    .actions {
        flex-direction: column;
        gap: 1rem;
    }
}
</style>
