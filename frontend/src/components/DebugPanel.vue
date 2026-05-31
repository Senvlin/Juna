<script setup>
defineProps({
    debugWordInfo: Object,
});
</script>

<template>
    <div v-if="debugWordInfo" class="debug-panel">
        <div class="debug-title">🐛 Debug</div>
        <div class="debug-row">
            <span class="debug-label">word</span>
            <span class="debug-val">{{ debugWordInfo.word }}</span>
        </div>
        <div class="debug-row">
            <span class="debug-label">type</span>
            <span class="debug-val">{{ debugWordInfo.type_of }}</span>
        </div>
        <div class="debug-row">
            <span class="debug-label">index</span>
            <span class="debug-val">{{ debugWordInfo.wordIndex }} /
                {{ debugWordInfo.totalInSequence }}</span>
        </div>
        <div class="debug-row">
            <span class="debug-label">failed_count</span>
            <span class="debug-val debug-num">{{ debugWordInfo.failed_count }}</span>
        </div>
        <div class="debug-row">
            <span class="debug-label">schedule</span>
            <span class="debug-val debug-num">{{ debugWordInfo.schedule }}</span>
        </div>
        <div class="debug-row">
            <span class="debug-label">isReady</span>
            <span class="debug-val">{{ debugWordInfo.isReady }}</span>
        </div>
        <div class="debug-row">
            <span class="debug-label">queue</span>
            <span class="debug-val">{{ debugWordInfo.reviewQueueSize }} 个待复习</span>
        </div>
        <div class="debug-row">
            <span class="debug-label">results</span>
            <span class="debug-val">{{ debugWordInfo.resultsCount }} 次</span>
        </div>
    </div>
</template>

<style scoped>
.debug-panel {
    position: fixed;
    top: 68px;
    right: 12px;
    z-index: 9999;
    background: rgba(0, 0, 0, 0.85);
    color: #0f0;
    font-family: "Cascadia Code", "Fira Code", monospace;
    font-size: 12px;
    line-height: 1.6;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid #0f0;
    min-width: 200px;
    backdrop-filter: blur(4px);
    pointer-events: none;
    user-select: none;
}

.debug-title {
    font-size: 13px;
    font-weight: bold;
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(0, 255, 0, 0.3);
    color: #0f0;
}

.debug-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
}

.debug-label {
    color: #8f8;
}

.debug-val {
    color: #fff;
    text-align: right;
    word-break: break-all;
}

.debug-num {
    color: #ff0;
    font-weight: bold;
    font-size: 14px;
}
</style>
