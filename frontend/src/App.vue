<script setup>
  import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
  import request from "./utils/request";

  // ========== 数据结构 ==========

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
      this.failed_count = 0;
      this.schedule = 0;
    }

    get groupedSenses() {
      return this.senses.map((s, i) => ({ ...s, index: i + 1 }));
    }

    get length() {
      return this.word.length;
    }

    get isReady() {
      return this.schedule >= 3;
    }

    markUnknown() {
      this.failed_count += 1;
    }

    markKnown() {
      if (this.failed_count === 0 && this.schedule === 0) {
        this.schedule = 3; // 从未失败的新词直接掌握
      } else if (this.schedule < 3) {
        this.schedule += 1;
      }
    }

    checkSpelling(charArray) {
      if (!charArray?.length) return { isCorrect: null };
      const typed = charArray.join("").toLowerCase().trim();
      if (!typed) return { isCorrect: null };
      return { isCorrect: typed === this.word.toLowerCase() };
    }
  }

  // ========== 所有状态 ==========

  const appState = ref("welcome");
  const userInput = ref("");
  const isCorrect = ref(null);
  const spellingMode = ref(false);
  const currentWordData = ref(null);
  const currentWordIndex = ref(0); // 当前在学习序列中的位置（0-based）
  const wordsData = ref([]); // 原始全部单词，只在此初始化，后面不再插入
  const notes = ref([]);
  const notesLoading = ref(false);
  const hasMoreNotes = ref(true);
  const progress = ref(0);
  const ukAudioRef = ref(null);
  const usAudioRef = ref(null);
  const notesContainerRef = ref(null);
  const spellingChars = ref([]);
  const spellingInputRef = ref(null);
  const wordResults = ref([]); // { word: Word, known: boolean }[]
  const learningStartTime = ref(0);
  const debugMode = ref(false);
  const debugCode = ref("");

  /** 复习队列：存放未掌握的单词 id */
  const reviewQueue = ref([]);

  /** Debug 模式：输入 "juna" 进入，显示单词属性 */
  const debugMode = ref(false);
  const debugCode = ref("");

  /** 学习序列总长：初始为原始词数，每插入一个复习词就 +1，保证进度条平滑 */
  const totalLearningCount = ref(0);

  const groupedSenses = computed(
    () => currentWordData.value?.groupedSenses ?? [],
  );

  const progressPercent = computed(() =>
    totalLearningCount.value > 0
      ? Math.round((currentWordIndex.value / totalLearningCount.value) * 100)
      : 0,
  );

  const currentBatch = computed(() => {
    const total = wordResults.value.length;
    const start = Math.max(0, total - 7);
    return wordResults.value.slice(start, total);
  });

  const debugWordInfo = computed(() => {
    const w = currentWordData.value;
    if (!w) return null;
    return {
      id: w.id,
      word: w.word,
      type_of: w.type_of,
      failed_count: w.failed_count,
      schedule: w.schedule,
      isReady: w.isReady,
      wordIndex: currentWordIndex.value,
      totalInSequence: totalLearningCount.value,
      reviewQueueSize: reviewQueue.value.length,
      resultsCount: wordResults.value.length,
    };
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

  function buildSyncPayload(words, startTime) {
    const buckets = {
      a_items: [],
      a_items_known: [],
      c_items: [],
      c_items_known: [],
    };

    for (const word of words) {
      const { id, failed_count, schedule, isReady, type_of, updated_at } = word;
      if (type_of === "NEW") {
        if (isReady) {
          buckets.a_items_known.push({
            failed_count: 0,
            item_id: id,
            schedule: 3,
          });
        } else {
          buckets.a_items.push({ failed_count, item_id: id, schedule });
        }
      } else {
        const base = { item_id: id, updated_at };
        if (isReady) {
          buckets.c_items_known.push({ ...base, failed_count: 0, schedule: 3 });
        } else {
          buckets.c_items.push({ ...base, failed_count, schedule });
        }
      }
    }

    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    return {
      ...buckets,
      date: new Date().toISOString().split("T")[0],
      learning_time: elapsed || 1,
    };
  }

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

  /**
   * 纯函数：根据队列和原始单词表，返回下一个要学习的词（或 null）
   * 规则：批次边界（每 7 个）且队列非空时优先队列；否则返回 words[nextRawIndex]
   */
  function getNextWord(words, rawIndex, queue, learnedCount) {
    // 如果处于批次边界（已学 7 的倍数），且有未掌握的复习词
    if (learnedCount > 0 && learnedCount % 7 === 0 && queue.length > 0) {
      const id = queue[0]; // 看一眼，不在这里 shift
      const found = words.find((w) => w.id === id);
      if (found) return { word: found, type: "review" };
    }
    // 正常取下一个原始词
    if (rawIndex < words.length) {
      return { word: words[rawIndex], type: "new" };
    }
    // 原始词用完了，但还有队列
    if (queue.length > 0) {
      const id = queue[0];
      const found = words.find((w) => w.id === id);
      if (found) return { word: found, type: "review" };
    }
    return null;
  }

  const shouldShowSummary = computed(() => {
    const count = wordResults.value.length;
    // 学完的单词数是 7 的倍数，且还有词可学
    if (count === 0) return false;
    if (count % 7 !== 0) return false;
    const next = getNextWord(
      wordsData.value,
      currentWordIndex.value + 1,
      reviewQueue.value,
      count,
    );
    return next !== null;
  });
  const resetWordUI = () => {
    spellingMode.value = false;
    isCorrect.value = null;
    userInput.value = "";
    spellingChars.value = [];
    notes.value = [];
    hasMoreNotes.value = true;
  };

  /** 设定当前展示的词，并更新索引与总数 */
  const setCurrentWord = (word) => {
    currentWordData.value = word;
  };

  const advanceToWord = (word, index) => {
    currentWordIndex.value = index;
    setCurrentWord(word);
    resetWordUI();
    appState.value = "learning";
  };

  const recordResult = (known) => {
    const word = currentWordData.value;
    wordResults.value.push({ word, known });

    if (known) {
      word.markKnown();
    } else {
      word.markUnknown();
    }

    // 未掌握且未在队列中才加入（避免重复）
    if (!word.isReady && !reviewQueue.value.includes(word.id)) {
      reviewQueue.value.push(word.id);
    }

    appState.value = "detail";
  };

  const getWordData = async () => {
    try {
      const list = await apiService.fetchWords();
      if (!list?.length) return;
      wordsData.value = list;
      totalLearningCount.value = list.length;
      currentWordData.value = list[0];
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
      const data = await apiService.fetchNotes(currentWordData.value);
      notes.value = data;
      hasMoreNotes.value = data.length >= 15;
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
    wordResults.value = [];
    await getWordData();
  };

  const handleKnown = async () => {
    recordResult(true);
    await fetchNotes();
  };

  const handleUnknown = async () => {
    recordResult(false);
    await fetchNotes();
  };

  const syncProgress = () => {
    const payload = buildSyncPayload(wordsData.value, learningStartTime.value);
    apiService.sync(payload).catch((err) => console.error("同步失败:", err));
  };

  const handleNext = () => {
    if (shouldShowSummary.value) {
      syncProgress();
      appState.value = "summary";
      return;
    }
    proceedToNext();
  };

  const proceedToNext = () => {
    const studiedCount = wordResults.value.length;
    const next = getNextWord(
      wordsData.value,
      currentWordIndex.value + 1,
      reviewQueue.value,
      studiedCount,
    );

    if (!next) {
      syncProgress();
      appState.value = "summary"; // 最后一批的总结
      return;
    }

    if (next.type === "review") {
      reviewQueue.value.shift();
      totalLearningCount.value += 1;
    }

    const newIndex = currentWordIndex.value + 1;
    currentWordIndex.value = newIndex;
    setCurrentWord(next.word);
    resetWordUI();
    appState.value = "learning";
  };

  const continueFromSummary = () => {
    // 如果最终总结之后已经没词了，进 completed
    const studiedCount = wordResults.value.length;
    const next = getNextWord(
      wordsData.value,
      currentWordIndex.value + 1,
      reviewQueue.value,
      studiedCount,
    );
    if (!next) {
      appState.value = "completed";
      return;
    }
    proceedToNext();
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
    // Debug 模式开关：依次按 j u n a 切换
    if (e.key.length === 1 && /[juna]/.test(e.key)) {
      debugCode.value += e.key;
      if (debugCode.value === "juna") {
        debugMode.value = !debugMode.value;
        debugCode.value = "";
      }
    } else if (debugCode.value) {
      debugCode.value = "";
    }

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
