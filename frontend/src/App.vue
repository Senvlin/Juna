<script setup>
  import { useLearning } from "./composables/useLearning";

  const {
    // 状态
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

    // 拼写状态
    spellingMode,
    isCorrect,
    spellingChars,
    spellingInputRef,

    // 音频
    ukAudioRef,
    usAudioRef,

    // 计算属性
    groupedSenses,
    progressPercent,
    currentBatch,

    // 方法
    startLearning,
    handleKnown,
    handleUnknown,
    handleNext,
    continueFromSummary,
    viewWordDetail,
    playAudio,
    onSpellingKeydown,
  } = useLearning();
</script>
<template>
  <!-- ====== Debug 面板（juna 开关） ====== -->
  <div v-if="debugMode && debugWordInfo" class="debug-panel">
    <div class="debug-title">🐛 Debug</div>
    <div class="debug-row">
      <span class="debug-label">word</span
      ><span class="debug-val">{{ debugWordInfo.word }}</span>
    </div>
    <div class="debug-row">
      <span class="debug-label">type</span
      ><span class="debug-val">{{ debugWordInfo.type_of }}</span>
    </div>
    <div class="debug-row">
      <span class="debug-label">index</span
      ><span class="debug-val"
        >{{ debugWordInfo.wordIndex }} /
        {{ debugWordInfo.totalInSequence }}</span
      >
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
      <span class="debug-label">isReady</span
      ><span class="debug-val">{{ debugWordInfo.isReady }}</span>
    </div>
    <div class="debug-row">
      <span class="debug-label">queue</span
      ><span class="debug-val"
        >{{ debugWordInfo.reviewQueueSize }} 个待复习</span
      >
    </div>
    <div class="debug-row">
      <span class="debug-label">results</span
      ><span class="debug-val">{{ debugWordInfo.resultsCount }} 次</span>
    </div>
  </div>

  <Teleport to="body">
    <button
      v-if="appState === 'detail'"
      class="next-btn-fixed"
      @click="handleNext"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="9 18 15 12 9 6"></polyline>
      </svg>
      {{ currentWordIndex + 1 >= totalLearningCount ? "完成" : "下一个" }}
      <kbd>Enter</kbd>
    </button>
  </Teleport>

  <!-- ========== 欢迎界面 ========== -->
  <div v-if="appState === 'welcome'" class="welcome-screen">
    <div class="welcome-icon">📖</div>
    <h1 class="welcome-title">单词学习系统</h1>
    <p class="welcome-subtitle">每天进步一点点，成就更好的自己</p>
    <button class="start-btn" @click="startLearning">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      开始今日单词学习
    </button>
    <p class="welcome-hint">按 <kbd>Enter</kbd> 开始</p>
  </div>

  <!-- ========== 学习界面 ========== -->
  <div v-else-if="appState === 'learning'" class="learning-mode">
    <!-- 进度条 -->
    <div class="progress-bar">
      <div
        class="progress-fill"
        :style="{ width: progressPercent + '%' }"
      ></div>
      <span class="progress-text"
        >{{ currentWordIndex + 1 }} / {{ totalLearningCount }}</span
      >
    </div>

    <!-- 单词展示 -->
    <div class="word_display">
      <template v-if="!spellingMode">
        <span class="word-text">{{ currentWordData?.word }}</span>
      </template>
      <template v-else>
        <div class="spelling-container">
          <div
            class="spelling-underscores"
            :class="{
              'is-correct': isCorrect === true,
              'is-incorrect': isCorrect === false,
            }"
          >
            <span
              v-for="(ch, i) in currentWordData?.word || ''"
              :key="i"
              class="underscore-char"
              :class="{
                filled: spellingChars[i],
                'is-correct': isCorrect === true,
                'is-incorrect': isCorrect === false,
              }"
              >{{ ch === " " ? " " : spellingChars[i] || "" }}</span
            >
          </div>
          <div v-if="isCorrect === true" class="spelling-status correct-status">
            ✓ 拼写正确！
          </div>
          <div
            v-else-if="isCorrect === false"
            class="spelling-status incorrect-status"
          >
            ✗ 拼写错误，再试一次
          </div>
          <input
            ref="spellingInputRef"
            type="text"
            class="spelling-hidden-input"
            :value="spellingChars.join('')"
            @keydown="onSpellingKeydown"
            autocomplete="off"
            autocapitalize="off"
            spellcheck="false"
          />
          <div v-if="spellingMode && spellingChars" class="action-hint">
            按 <kbd>Esc</kbd> 退出拼写模式
          </div>
        </div>
      </template>
    </div>

    <!-- 音频区域 -->
    <div id="audio-section" v-if="!spellingMode">
      <div class="audio-item" v-if="currentWordData?.audio_uk_url">
        <audio
          :src="currentWordData.audio_uk_url"
          ref="ukAudioRef"
          preload="auto"
        ></audio>
        <span class="ipa-label">英 /{{ currentWordData?.ipa_uk }}/</span>
        <button class="icon-btn" @click="playAudio('uk')" title="播放英式发音">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
            <path
              d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"
            ></path>
          </svg>
        </button>
      </div>
      <div class="audio-item" v-if="currentWordData?.audio_us_url">
        <audio
          :src="currentWordData.audio_us_url"
          ref="usAudioRef"
          preload="auto"
        ></audio>
        <span class="ipa-label">美 /{{ currentWordData?.ipa_us }}/</span>
        <button class="icon-btn" @click="playAudio('us')" title="播放美式发音">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
            <path
              d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"
            ></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div v-if="!spellingMode" class="action-hint">
      按 <kbd>Enter</kbd> 进入拼写模式
    </div>
    <div v-if="!spellingMode" class="action-buttons">
      <button class="action-btn known" @click="handleKnown">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        认识 <kbd>1</kbd>
      </button>
      <button class="action-btn unknown" @click="handleUnknown">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
        不认识 <kbd>2</kbd>
      </button>
    </div>
  </div>

  <!-- ========== 详情界面 ========== -->
  <div v-else-if="appState === 'detail'" class="detail-mode">
    <!-- 进度条 -->
    <div class="progress-bar">
      <div
        class="progress-fill"
        :style="{ width: progressPercent + '%' }"
      ></div>
      <span class="progress-text"
        >{{ currentWordIndex + 1 }} / {{ totalLearningCount }}</span
      >
    </div>

    <!-- 单词头部 -->
    <div class="detail-header">
      <h2 class="detail-word">{{ currentWordData?.word }}</h2>
      <div class="detail-phonetics">
        <span class="phonetic-item" v-if="currentWordData?.audio_uk_url">
          <audio
            :src="currentWordData.audio_uk_url"
            ref="ukAudioRef"
            preload="auto"
          ></audio>
          英 /{{ currentWordData?.ipa_uk }}/
          <button class="mini-audio-btn" @click="playAudio('uk')">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
            </svg>
          </button>
        </span>
        <span class="phonetic-item" v-if="currentWordData?.audio_us_url">
          <audio
            :src="currentWordData.audio_us_url"
            ref="usAudioRef"
            preload="auto"
          ></audio>
          美 /{{ currentWordData?.ipa_us }}/
          <button class="mini-audio-btn" @click="playAudio('us')">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
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
        <div
          v-for="sense in groupedSenses"
          :key="sense.index"
          class="sense-item"
        >
          <span class="sense-pos">{{ sense.pos }}</span>
          <span class="sense-def">{{ sense.definition_cn }}</span>
        </div>
      </div>
    </div>

    <!-- 笔记区域 -->
    <div class="notes-section">
      <h3 class="section-title">
        用户笔记
        <span class="notes-count" v-if="notes.length"
          >({{ notes.length }})</span
        >
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
            <p
              v-for="(line, li) in note.content.split('\n')"
              :key="li"
              class="note-line"
            >
              {{ line }}
            </p>
          </div>
          <div class="note-footer">
            <span class="note-author" v-if="note.user_info?.nickname">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
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
  <!-- 这里补上了 detail-mode 的闭合标签 -->

  <!-- ========== 总结界面 ========== -->
  <div v-else-if="appState === 'summary'" class="summary-screen">
    <!-- 进度条 -->
    <div class="progress-bar">
      <div
        class="progress-fill"
        :style="{ width: progressPercent + '%' }"
      ></div>
      <span class="progress-text"
        >{{ wordResults.length }} / {{ totalLearningCount }}</span
      >
    </div>

    <div class="summary-header">
      <h2 class="summary-title">小总结</h2>
      <p class="summary-subtitle">
        认识了 {{ currentBatch.filter((r) => r.known).length }} 个，还需复习
        {{ currentBatch.filter((r) => !r.known).length }} 个
      </p>
    </div>

    <div class="summary-list">
      <div
        v-for="(result, idx) in currentBatch"
        :key="idx"
        class="summary-card"
        :class="{ known: result.known, unknown: !result.known }"
        @click="viewWordDetail(result)"
        role="button"
        tabindex="0"
      >
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
      <button
        class="action-btn summary-continue-btn"
        @click="continueFromSummary"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
        {{
          currentWordIndex + 1 >= totalLearningCount ? "完成学习" : "继续学习"
        }}
        <kbd>Enter</kbd>
      </button>
    </div>
  </div>

  <!-- ========== 完成界面 ========== -->
  <div v-else-if="appState === 'completed'" class="completion-screen">
    <div class="completion-icon">🎉</div>
    <h2>今日单词学习完成！</h2>
    <p class="completion-stats">
      你已完成了 <strong>{{ totalLearningCount }}</strong> 个单词的学习
    </p>
    <button class="action-btn completion-btn" @click="appState = 'welcome'">
      返回首页 <kbd>Enter</kbd>
    </button>
  </div>
</template>

<style>
  @import "./style.css";

  /* Debug 面板 */
  .debug-panel {
    position: fixed;
    top: 12px;
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
