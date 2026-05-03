<script setup>
  import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
  import request from "./utils/request";

  class Word {
    constructor(data) {
      this.id = data.id;
      this.word = data.word;
      this.ipa_uk = data.ipa_uk;
      this.ipa_us = data.ipa_us;
      this.audio_uk_url = data.audio_uk_url;
      this.audio_us_url = data.audio_us_url;
      this.type_of = data.type_of;
      this.updated_at = data.updated_at;
      this.senses = data.senses || [];
      // 学习状态（新单词初始为 0）
      this.failed_count = 0;
      this.schedule = 0;
    }

    get groupedSenses() {
      return this.senses.map((s, i) => ({ ...s, index: i + 1 }));
    }

    get length() {
      return this.word.length;
    }

    /** schedule >= 3 即为已掌握，放入 sync 的 known 列表 */
    get isReady() {
      return this.schedule >= 3;
    }

    /** 点"不认识" → failed_count += 1 */
    markUnknown() {
      this.failed_count += 1;
    }

    /** 点"认识" → schedule += 1（上限 3） */
    markKnown() {
      if (this.schedule < 3) this.schedule += 1;
    }

    checkSpelling(charArray) {
      if (!charArray?.length) return { isCorrect: null };
      const typed = charArray.join("").toLowerCase().trim();
      if (!typed) return { isCorrect: null };
      return { isCorrect: typed === this.word.toLowerCase() };
    }
  }

  const appState = ref("welcome"); // 'welcome' | 'learning' | 'detail' | 'summary' | 'completed'
  const userInput = ref("");
  const isCorrect = ref(null);
  const spellingMode = ref(false);
  const currentWordData = ref(null);
  const currentWordIndex = ref(0);
  const wordsData = ref([]);
  const notes = ref([]);
  const notesLoading = ref(false);
  const hasMoreNotes = ref(true);
  const progress = ref(0);
  const ukAudioRef = ref(null);
  const usAudioRef = ref(null);
  const notesContainerRef = ref(null);
  const spellingChars = ref([]);
  const spellingInputRef = ref(null);
  const wordResults = ref([]); // { word, known }[]
  const learningStartTime = ref(0);

  /** 待复习的单词 ID 队列（不认识但还需要继续练） */
  const reviewQueue = ref([]);

  const totalWords = computed(() => wordsData.value.length);

  const progressPercent = computed(() =>
    totalWords.value > 0
      ? Math.round((currentWordIndex.value / totalWords.value) * 100)
      : 0,
  );

  const groupedSenses = computed(
    () => currentWordData.value?.groupedSenses ?? [],
  );

  const currentBatch = computed(() => {
    const total = wordResults.value.length;
    const start = Math.max(0, total - 7);
    return wordResults.value.slice(start, total);
  });

  const audioService = {
    play(refEl) {
      if (!refEl?.value) return;
      refEl.value.currentTime = 0;
      refEl.value.play().catch(() => {});
    },
  };

  const apiService = {
    async fetchWords() {
      const [newResp, reviewResp] = await Promise.all([
        request.get("/word/new"),
        request.get("/word/review"),
      ]);
      const rawList = [...(reviewResp.data || []), ...(newResp.data || [])];
      return rawList.map((raw) => new Word(raw));
    },
    async fetchNotes(wordData) {
      const resp = await request.post("/word/note/", wordData);
      return resp.data || [];
    },
    async sync(payload) {
      await request.post("/word/sync", payload);
    },
  };

  const syncService = {
    buildPayload(words, startTime) {
      const buckets = {
        a_items: [],
        a_items_known: [],
        c_items: [],
        c_items_known: [],
      };

      for (const word of words) {
        const { failed_count, schedule, isReady, type_of, updated_at } = word;
        const isNew = type_of === "NEW";

        if (isNew) {
          if (isReady) {
            buckets.a_items_known.push({
              failed_count: 0,
              item_id: word.id,
              schedule: 3,
            });
          } else {
            buckets.a_items.push({
              failed_count,
              item_id: word.id,
              schedule,
            });
          }
        } else {
          const base = { item_id: word.id, updated_at };
          if (isReady) {
            buckets.c_items_known.push({
              ...base,
              failed_count: 0,
              schedule: 3,
            });
          } else {
            buckets.c_items.push({
              ...base,
              failed_count,
              schedule,
            });
          }
        }
      }

      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      return {
        ...buckets,
        date: new Date().toISOString().split("T")[0],
        learning_time: elapsed || 1,
      };
    },
  };

  const spellingService = {
    handleKey(e, charArray, wordLen) {
      if (e.key === "Enter") {
        e.preventDefault();
        return { action: "check", chars: charArray };
      }
      if (e.key === "Backspace") {
        e.preventDefault();
        return { action: "update", chars: charArray.slice(0, -1) };
      }
      if (
        e.key.length === 1 &&
        /[a-zA-Z]/.test(e.key) &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey
      ) {
        e.preventDefault();
        if (charArray.length < wordLen) {
          return { action: "update", chars: [...charArray, e.key] };
        }
      }
      return { action: "none", chars: charArray };
    },
  };

  const sessionService = {
    resetWordState() {
      spellingMode.value = false;
      isCorrect.value = null;
      userInput.value = "";
      spellingChars.value = [];
      notes.value = [];
      hasMoreNotes.value = true;
    },

    advanceTo(index) {
      currentWordIndex.value = index;
      currentWordData.value = wordsData.value[index];
      progress.value = index;
      this.resetWordState();
      appState.value = "learning";
    },

    recordResult(known) {
      const word = currentWordData.value;
      wordResults.value.push({ word, known });

      if (known) {
        word.markKnown();
      } else {
        word.markUnknown();
      }

      // 只要还没掌握（schedule < 3），就持续进入复习队列
      if (!word.isReady && !reviewQueue.value.includes(word.id)) {
        reviewQueue.value.push(word.id);
      }

      appState.value = "detail";
    },
  };

  const playAudio = (type) => {
    audioService.play(type === "uk" ? ukAudioRef : usAudioRef);
  };

  const getWordData = async () => {
    try {
      const wordList = await apiService.fetchWords();
      if (!wordList?.length) return;
      wordsData.value = wordList;
      currentWordData.value = wordList[0];
      currentWordIndex.value = 0;
      progress.value = 0;
    } catch (err) {
      console.error("获取单词失败:", err);
    }
  };

  const fetchNotes = async () => {
    if (!currentWordData.value || notesLoading.value || !hasMoreNotes.value)
      return;
    notesLoading.value = true;
    try {
      const list = await apiService.fetchNotes(currentWordData.value);
      notes.value = list;
      hasMoreNotes.value = list.length >= 15;
    } catch (err) {
      console.error("获取笔记失败:", err);
      notes.value = [];
    } finally {
      notesLoading.value = false;
    }
  };

  const startLearning = async () => {
    appState.value = "learning";
    learningStartTime.value = Date.now();
    reviewQueue.value = [];
    await getWordData();
  };

  const handleKnown = async () => {
    sessionService.recordResult(true);
    await fetchNotes();
  };

  const handleUnknown = async () => {
    sessionService.recordResult(false);
    await fetchNotes();
  };

  const handleNext = () => {
    const studiedCount = wordResults.value.length;
    const isBatchBoundary = studiedCount > 0 && studiedCount % 7 === 0;
    const nextIdx = currentWordIndex.value + 1;
    let hasMore = nextIdx < wordsData.value.length;

    // 每学完 7 个词，插入一个待复习的单词
    if (isBatchBoundary && reviewQueue.value.length > 0) {
      const reviewId = reviewQueue.value.shift();
      const reviewWord = wordsData.value.find((w) => w.id === reviewId);
      if (reviewWord) {
        wordsData.value.splice(nextIdx, 0, reviewWord);
        hasMore = true;
      }
    }

    // 到末尾了但还有复习词 → 插到末尾继续学
    if (!hasMore && reviewQueue.value.length > 0) {
      const reviewId = reviewQueue.value.shift();
      const reviewWord = wordsData.value.find((w) => w.id === reviewId);
      if (reviewWord) {
        wordsData.value.push(reviewWord);
        hasMore = true;
      }
    }

    // 每 7 个词或已无剩余词 → 同步 + 总结
    if ((studiedCount > 0 && studiedCount % 7 === 0) || !hasMore) {
      const payload = syncService.buildPayload(
        wordsData.value,
        learningStartTime.value,
      );
      apiService
        .sync(payload)
        .catch((err) => console.error("同步到扇贝服务器失败:", err));
      appState.value = "summary";
      return;
    }

    sessionService.advanceTo(nextIdx);
  };

  const continueFromSummary = () => {
    const nextIdx = currentWordIndex.value + 1;
    if (nextIdx < wordsData.value.length) {
      sessionService.advanceTo(nextIdx);
    } else {
      appState.value = "completed";
    }
  };

  const viewWordDetail = async (result) => {
    currentWordData.value = result.word;
    appState.value = "detail";
    notes.value = [];
    hasMoreNotes.value = true;
    await fetchNotes();
  };

  // ====== 拼写相关方法 ======
  const checkSpelling = () => {
    const word = currentWordData.value;
    const result = word?.checkSpelling(spellingChars.value) ?? {
      isCorrect: null,
    };
    isCorrect.value = result.isCorrect;

    const resetAfter = (ms) =>
      setTimeout(() => {
        spellingMode.value = false;
        isCorrect.value = null;
        spellingChars.value = [];
        userInput.value = "";
      }, ms);

    if (result.isCorrect === true) {
      resetAfter(1200);
    } else if (result.isCorrect === false) {
      setTimeout(() => {
        if (
          spellingChars.value.length >= (currentWordData.value?.length ?? 0)
        ) {
          isCorrect.value = null;
          spellingChars.value = [];
          userInput.value = "";
        }
      }, 1200);
    }
  };

  const onSpellingKeydown = (e) => {
    const word = currentWordData.value;
    const wordLen = word?.length ?? 0;
    const { action, chars } = spellingService.handleKey(
      e,
      spellingChars.value,
      wordLen,
    );

    if (action === "update") {
      isCorrect.value = null;
      spellingChars.value = chars;
      if (chars.length === word.length) {
        checkSpelling();
      }
    } else if (action === "check") {
      checkSpelling();
    }
  };

  // ====== 键盘路由 ======
  const handleKeyDown = (e) => {
    const handlers = {
      welcome: () => {
        if (e.key === "Enter") startLearning();
      },
      learning: () => {
        if (e.key === "1") handleKnown();
        else if (e.key === "2") handleUnknown();
        else if (e.key === "Enter" && !spellingMode.value) {
          spellingMode.value = true;
          spellingChars.value = [];
          isCorrect.value = null;
          nextTick(() => spellingInputRef.value?.focus());
        } else if (e.key === "Escape" && spellingMode.value) {
          e.preventDefault();
          spellingMode.value = false;
          isCorrect.value = null;
          spellingChars.value = [];
          userInput.value = "";
        }
      },
      detail: () => {
        if (e.key === "Enter") handleNext();
      },
      summary: () => {
        if (e.key === "Enter") continueFromSummary();
      },
      completed: () => {
        if (e.key === "Enter") appState.value = "welcome";
      },
    };
    handlers[appState.value]?.();
  };

  onMounted(() => window.addEventListener("keydown", handleKeyDown));
  onUnmounted(() => window.removeEventListener("keydown", handleKeyDown));
</script>
<template>
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
      {{ currentWordIndex + 1 >= totalWords ? "完成" : "下一个" }}
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
        >{{ currentWordIndex + 1 }} / {{ totalWords }}</span
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
        >{{ currentWordIndex + 1 }} / {{ totalWords }}</span
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
        >{{ wordResults.length }} / {{ totalWords }}</span
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
        {{ currentWordIndex + 1 >= totalWords ? "完成学习" : "继续学习" }}
        <kbd>Enter</kbd>
      </button>
    </div>
  </div>

  <!-- ========== 完成界面 ========== -->
  <div v-else-if="appState === 'completed'" class="completion-screen">
    <div class="completion-icon">🎉</div>
    <h2>今日单词学习完成！</h2>
    <p class="completion-stats">
      你已完成了 <strong>{{ totalWords }}</strong> 个单词的学习
    </p>
    <button class="action-btn completion-btn" @click="appState = 'welcome'">
      返回首页 <kbd>Enter</kbd>
    </button>
  </div>
</template>

<style>
  @import "./style.css";
</style>
