<script setup>
import { inject } from "vue";

const {
    appState,
    currentWordData,
    currentWordIndex,
    notes,
    notesLoading,
    hasMoreNotes,
    wordResults,
    totalLearningCount,
    debugMode,
    debugWordInfo,
    notesContainerRef,
    spellingMode,
    isCorrect,
    spellingChars,
    spellingInputRef,
    groupedSenses,
    progressPercent,
    currentBatch,
    startLearning,
    handleKnown,
    handleUnknown,
    handleNext,
    continueFromSummary,
    viewWordDetail,
    playAudio,
    onSpellingKeydown,
} = inject("learning");
</script>

<template>
    <!-- ========== 学习界面 ========== -->
    <div v-if="appState === 'learning'" class="learning-mode">
        <div class="learning-content">
            <!-- 进度条 -->
            <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
                <span class="progress-text">{{ currentWordIndex + 1 }} / {{ totalLearningCount }}</span>
            </div>

            <!-- 单词展示 -->
            <div class="word_display">
                <template v-if="!spellingMode">
                    <span class="word-text">{{ currentWordData?.word }}</span>
                </template>
                <template v-else>
                    <div class="spelling-container">
                        <div class="spelling-underscores" :class="{
                            'is-correct': isCorrect === true,
                            'is-incorrect': isCorrect === false,
                        }">
                            <span v-for="(ch, i) in currentWordData?.word || ''" :key="i" class="underscore-char" :class="{
                                filled: spellingChars[i],
                                'is-correct': isCorrect === true,
                                'is-incorrect': isCorrect === false,
                            }">{{ ch === " " ? " " : spellingChars[i] || "" }}</span>
                        </div>
                        <div v-if="isCorrect === true" class="spelling-status correct-status">
                            ✓ 拼写正确！
                        </div>
                        <div v-else-if="isCorrect === false" class="spelling-status incorrect-status">
                            ✗ 拼写错误，再试一次
                        </div>
                        <input ref="spellingInputRef" type="text" class="spelling-hidden-input" :value="spellingChars.join('')" @keydown="onSpellingKeydown" autocomplete="off" autocapitalize="off" spellcheck="false" />
                        <div v-if="spellingMode && spellingChars" class="action-hint">
                            按 <kbd>Esc</kbd> 退出拼写模式
                        </div>
                    </div>
                </template>
            </div>

            <!-- 音频区域 -->
            <div id="audio-section" v-if="!spellingMode">
                <div class="audio-item" v-if="currentWordData?.audio_uk_url">
                    <audio :src="currentWordData.audio_uk_url" preload="auto"></audio>
                    <span class="ipa-label">英 /{{ currentWordData?.ipa_uk }}/</span>
                    <button class="icon-btn" @click="playAudio('uk')" title="播放英式发音">
                        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                        </svg>
                    </button>
                </div>
                <div class="audio-item" v-if="currentWordData?.audio_us_url">
                    <audio :src="currentWordData.audio_us_url" preload="auto"></audio>
                    <span class="ipa-label">美 /{{ currentWordData?.ipa_us }}/</span>
                    <button class="icon-btn" @click="playAudio('us')" title="播放美式发音">
                        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- 操作提示 -->
            <div v-if="!spellingMode" class="action-hint">
                按 <kbd>Enter</kbd> 进入拼写模式
            </div>

            <!-- 操作按钮 -->
            <div v-if="!spellingMode" class="action-buttons">
                <button class="action-btn known" @click="handleKnown">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    认识 <kbd>1</kbd>
                </button>
                <button class="action-btn unknown" @click="handleUnknown">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                    不认识 <kbd>2</kbd>
                </button>
            </div>
        </div>
    </div>

    <!-- ========== 详情界面 ========== -->
    <div v-else-if="appState === 'detail'" class="detail-mode">
        <div class="detail-content">
            <!-- 进度条 -->
            <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
                <span class="progress-text">{{ currentWordIndex + 1 }} / {{ totalLearningCount }}</span>
            </div>

            <!-- 单词头部 -->
            <div class="detail-header">
                <h2 class="detail-word">{{ currentWordData?.word }}</h2>
                <div class="detail-phonetics">
                    <span class="phonetic-item" v-if="currentWordData?.audio_uk_url">
                        <audio :src="currentWordData.audio_uk_url" preload="auto"></audio>
                        英 /{{ currentWordData?.ipa_uk }}/
                        <button class="mini-audio-btn" @click="playAudio('uk')">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                            </svg>
                        </button>
                    </span>
                    <span class="phonetic-item" v-if="currentWordData?.audio_us_url">
                        <audio :src="currentWordData.audio_us_url" preload="auto"></audio>
                        美 /{{ currentWordData?.ipa_us }}/
                        <button class="mini-audio-btn" @click="playAudio('us')">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                            </svg>
                        </button>
                    </span>
                </div>
            </div>

            <!-- 释义区域 -->
            <div class="senses-section">
                <h3 class="section-title">释义</h3>
                <div class="senses-list">
                    <div v-for="sense in groupedSenses" :key="sense.index" class="sense-item">
                        <span class="sense-pos">{{ sense.pos }}</span>
                        <span class="sense-def">{{ sense.definition_cn }}</span>
                    </div>
                </div>
            </div>

            <!-- 笔记区域 -->
            <div class="notes-section">
                <h3 class="section-title">
                    用户笔记
                    <span class="notes-count" v-if="notes.length">({{ notes.length }})</span>
                </h3>

                <div v-if="notesLoading" class="notes-loading">
                    <div class="loading-spinner"></div>
                    <span>加载笔记中...</span>
                </div>

                <div v-else-if="notes.length === 0" class="notes-empty">
                    <p>暂无其他用户的笔记</p>
                </div>

                <div v-else ref="notesContainerRef" class="notes-grid">
                    <div v-for="note in notes" :key="note.id" class="note-card">
                        <div class="note-content">
                            <p v-for="(line, li) in note.content.split('\n')" :key="li" class="note-line">
                                {{ line }}
                            </p>
                        </div>
                        <div class="note-footer">
                            <span class="note-author" v-if="note.user_info?.nickname">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                    <circle cx="12" cy="7" r="4"></circle>
                                </svg>
                                {{ note.user_info.nickname }}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ========== 总结界面 ========== -->
    <div v-else-if="appState === 'summary'" class="summary-screen">
        <div class="summary-content">
            <!-- 进度条 -->
            <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
                <span class="progress-text">{{ wordResults.length }} / {{ totalLearningCount }}</span>
            </div>

            <div class="summary-header">
                <h2 class="summary-title">小总结</h2>
                <p class="summary-subtitle">
                    认识了
                    {{currentBatch.filter((r) => r.known).length}} 个，还需复习
                    {{currentBatch.filter((r) => !r.known).length}} 个
                </p>
            </div>

            <div class="summary-list">
                <div v-for="(result, idx) in currentBatch" :key="idx" class="summary-card" :class="{ known: result.known, unknown: !result.known }" @click="viewWordDetail(result)" role="button" tabindex="0">
                    <div class="summary-card-left">
                        <span class="summary-card-word">{{ result.word.word }}</span>
                        <span class="summary-card-senses">
                            {{
                                result.word.senses
                                    ?.map((s) => s.pos + " " + s.definition_cn)
                                    .join("；") || ""
                            }}
                        </span>
                    </div>
                    <div class="summary-card-tag">
                        {{ result.known ? "认识" : "不认识" }}
                    </div>
                </div>
            </div>

            <div class="summary-actions">
                <button class="action-btn summary-continue-btn" @click="continueFromSummary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                    {{
                        currentWordIndex + 1 >= totalLearningCount ? "完成学习" : "继续学习"
                    }}
                    <kbd>Enter</kbd>
                </button>
            </div>
        </div>
    </div>

    <!-- ========== 完成界面 ========== -->
    <div v-else-if="appState === 'completed'" class="completion-screen">
        <div class="completion-content">
            <div class="completion-icon">🎉</div>
            <h2>今日单词学习完成！</h2>
            <p class="completion-stats">
                你已完成了 <strong>{{ totalLearningCount }}</strong> 个单词的学习
            </p>
            <button class="action-btn completion-btn" @click="appState = 'welcome'">
                返回首页 <kbd>Enter</kbd>
            </button>
        </div>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="appState === 'loading'" class="learning-mode" style="display: flex; justify-content: center; align-items: center">
        <div class="loading-spinner"></div>
        <span style="color: #9ca3af; margin-left: 1rem">加载学习中...</span>
    </div>
</template>

<style scoped>
/* ====== 布局容器 ====== */
.learning-content,
.detail-content,
.summary-content,
.completion-content {
    max-width: 640px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
}

/* ====== 页面容器统一样式 ====== */
.learning-mode,
.detail-mode,
.summary-screen,
.completion-screen {
    min-height: 100vh;
    width: 100%;
    background: radial-gradient(ellipse at 20% 30%, #111827, #030712);
    position: relative;
    overflow-x: hidden;
}

/* 噪点纹理 */
.learning-mode::before,
.detail-mode::before,
.summary-screen::before,
.completion-screen::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
}

.learning-mode>*,
.detail-mode>*,
.summary-screen>*,
.completion-screen>* {
    position: relative;
    z-index: 2;
}

/* ====== 进度条 ====== */
.progress-bar {
    position: relative;
    background: rgba(31, 41, 55, 0.6);
    backdrop-filter: blur(8px);
    height: 8px;
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 2rem;
}

.progress-fill {
    height: 100%;
    border-radius: 20px;
    background: linear-gradient(90deg, #4f46e5, #7c3aed);
    transition: width 0.4s ease;
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
}

.progress-text {
    position: absolute;
    right: 0;
    top: -1.5rem;
    font-size: 0.8rem;
    color: #9ca3af;
    font-weight: 500;
}

/* ====== 单词展示 ====== */
.word_display {
    text-align: center;
    margin: 2.5rem 0;
}

.word-text {
    font-size: 3.5rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #e0e7ff;
    text-shadow: 0 0 30px rgba(99, 102, 241, 0.3);
}

/* ====== 拼写模式 ====== */
.spelling-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
}

.spelling-underscores {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.25rem;
    padding: 1.5rem;
    border-radius: 16px;
    background: rgba(15, 18, 30, 0.5);
    border: 1px solid rgba(99, 102, 241, 0.15);
    transition: all 0.3s ease;
}

.spelling-underscores.is-correct {
    border-color: rgba(16, 185, 129, 0.4);
    background: rgba(16, 185, 129, 0.05);
}

.spelling-underscores.is-incorrect {
    border-color: rgba(239, 68, 68, 0.4);
    background: rgba(239, 68, 68, 0.05);
}

.underscore-char {
    width: 2rem;
    height: 2.8rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    font-weight: 700;
    color: #1f2937;
    border-bottom: 3px solid #374151;
    transition: all 0.2s ease;
    font-family: "Courier New", monospace;
}

.underscore-char.filled {
    color: #e0e7ff;
    border-bottom-color: #6366f1;
}

.underscore-char.is-correct {
    color: #10b981;
    border-bottom-color: #10b981;
}

.underscore-char.is-incorrect {
    color: #ef4444;
    border-bottom-color: #ef4444;
}

.spelling-status {
    font-size: 1rem;
    font-weight: 600;
}

.correct-status {
    color: #10b981;
}

.incorrect-status {
    color: #ef4444;
}

.spelling-hidden-input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
    pointer-events: none;
}

/* ====== 音频区域 ====== */
#audio-section {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin: 1.5rem 0;
}

.audio-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.ipa-label {
    color: #9ca3af;
    font-size: 0.95rem;
    font-family: "Times New Roman", serif;
}

.icon-btn {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: #818cf8;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
}

.icon-btn:hover {
    background: rgba(99, 102, 241, 0.2);
    transform: scale(1.1);
}

/* ====== 操作按钮 ====== */
.action-hint {
    text-align: center;
    color: #6b7280;
    font-size: 0.9rem;
    margin: 1rem 0;
}

.action-hint kbd {
    background: #1f2937;
    border-radius: 4px;
    padding: 0.15rem 0.4rem;
    font-size: 0.75rem;
    color: #cbd5e1;
}

.action-buttons {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 1.5rem;
}

.action-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.8rem 1.8rem;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 12px;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
}

.action-btn kbd {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    padding: 0.1rem 0.35rem;
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.7);
}

.action-btn.known {
    background: linear-gradient(90deg, #059669, #10b981);
    color: white;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.action-btn.known:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.action-btn.unknown {
    background: linear-gradient(90deg, #dc2626, #ef4444);
    color: white;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.action-btn.unknown:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

/* ====== 详情页 ====== */
.detail-header {
    margin-bottom: 2rem;
}

.detail-word {
    font-size: 2.8rem;
    font-weight: 800;
    color: #e0e7ff;
    margin-bottom: 0.5rem;
}

.detail-phonetics {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
}

.phonetic-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    color: #9ca3af;
    font-size: 1rem;
    font-family: "Times New Roman", serif;
}

.mini-audio-btn {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: #818cf8;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
}

.mini-audio-btn:hover {
    background: rgba(99, 102, 241, 0.2);
}

/* 释义 */
.senses-section {
    margin-bottom: 2rem;
}

.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #9ca3af;
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.senses-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.sense-item {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
    padding: 0.6rem 1rem;
    background: rgba(15, 18, 30, 0.4);
    border-radius: 8px;
    border: 1px solid rgba(99, 102, 241, 0.08);
}

.sense-pos {
    font-size: 0.8rem;
    font-weight: 600;
    color: #818cf8;
    background: rgba(99, 102, 241, 0.12);
    padding: 0.1rem 0.5rem;
    border-radius: 4px;
    flex-shrink: 0;
}

.sense-def {
    color: #d1d5db;
    font-size: 0.95rem;
    line-height: 1.5;
}

/* 笔记 */
.notes-loading {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: #9ca3af;
    padding: 1rem;
}

.loading-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(99, 102, 241, 0.2);
    border-top-color: #6366f1;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.notes-empty {
    color: #6b7280;
    padding: 1rem;
    text-align: center;
}

.notes-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.note-card {
    background: rgba(15, 18, 30, 0.4);
    border: 1px solid rgba(99, 102, 241, 0.1);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    transition: border-color 0.2s;
}

.note-card:hover {
    border-color: rgba(99, 102, 241, 0.25);
}

.note-content {
    margin-bottom: 0.5rem;
}

.note-line {
    color: #d1d5db;
    font-size: 0.9rem;
    line-height: 1.6;
}

.note-footer {
    display: flex;
    justify-content: flex-end;
}

.note-author {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.8rem;
    color: #6b7280;
}

/* ====== 总结界面 ====== */
.summary-header {
    text-align: center;
    margin-bottom: 1.5rem;
}

.summary-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: #e0e7ff;
    margin-bottom: 0.5rem;
}

.summary-subtitle {
    color: #9ca3af;
    font-size: 0.95rem;
}

.summary-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}

.summary-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid rgba(99, 102, 241, 0.1);
}

.summary-card:hover {
    border-color: rgba(99, 102, 241, 0.3);
    background: rgba(15, 18, 30, 0.5);
}

.summary-card.known {
    border-left: 3px solid #10b981;
}

.summary-card.unknown {
    border-left: 3px solid #ef4444;
}

.summary-card-left {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.summary-card-word {
    font-weight: 700;
    font-size: 1rem;
    color: #e0e7ff;
}

.summary-card-senses {
    font-size: 0.8rem;
    color: #6b7280;
    display: -webkit-box;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.summary-card-tag {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    flex-shrink: 0;
}

.known .summary-card-tag {
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
}

.unknown .summary-card-tag {
    background: rgba(239, 68, 68, 0.12);
    color: #ef4444;
}

.summary-actions {
    text-align: center;
}

.summary-continue-btn {
    background: linear-gradient(90deg, #4f46e5, #7c3aed);
    color: white;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
}

.summary-continue-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
}

/* ====== 完成界面 ====== */
.completion-screen {
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
}

.completion-icon {
    font-size: 5rem;
    margin-bottom: 1rem;
    animation: bounce 1s ease infinite;
}

@keyframes bounce {

    0%,
    100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-10px);
    }
}

.completion-screen h2 {
    font-size: 2rem;
    font-weight: 700;
    color: #e0e7ff;
    margin-bottom: 0.75rem;
}

.completion-stats {
    color: #9ca3af;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

.completion-stats strong {
    color: #818cf8;
}

.completion-btn {
    background: linear-gradient(90deg, #4f46e5, #7c3aed);
    color: white;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
}

.completion-btn:hover {
    transform: translateY(-2px);
}

/* 响应式 */
@media (max-width: 640px) {
    .word-text {
        font-size: 2.5rem;
    }

    .action-buttons {
        flex-direction: column;
        align-items: center;
    }

    .action-btn {
        width: 100%;
        justify-content: center;
    }
}
</style>
