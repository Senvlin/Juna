import { ref, computed, onMounted, onUnmounted } from "vue";
import { Word } from "./useWord";
import { useAudio } from "./useAudio";
import { useSpelling } from "./useSpelling";
import { apiService } from "../utils/api";
import { buildSyncPayload, getNextWord } from "../utils/helpers";

/**
 * 核心学习逻辑 composable
 * 整合所有子 composable 和工具函数，暴露模板所需的所有状态与方法
 */
export function useLearning() {
  // ====== 子 composables ======
  const { ukAudioRef, usAudioRef, playAudio } = useAudio();

  const {
    spellingMode,
    isCorrect,
    spellingChars,
    spellingInputRef,
    onSpellingKeydown: rawOnSpellingKeydown,
    enterSpellingMode,
    exitSpellingMode,
    resetSpelling,
  } = useSpelling();

  // ====== 核心状态 ======
  const appState = ref("welcome");
  const currentWordData = ref(null);
  const currentWordIndex = ref(0);
  const wordsData = ref([]);
  const notes = ref([]);
  const notesLoading = ref(false);
  const hasMoreNotes = ref(true);
  const wordResults = ref([]);
  const learningStartTime = ref(0);
  const reviewQueue = ref([]);
  const totalLearningCount = ref(0);
  const progress = ref(0);
  const notesContainerRef = ref(null);
  const userInput = ref("");
  const debugMode = ref(false);
  const debugCode = ref("");

  // ====== 计算属性 ======
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

  const shouldShowSummary = computed(() => {
    const count = wordResults.value.length;
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

  // ====== 内部方法 ======

  function resetWordUI() {
    resetSpelling();
    userInput.value = "";
    notes.value = [];
    hasMoreNotes.value = true;
  }

  function setCurrentWord(word) {
    currentWordData.value = word;
  }

  function recordResult(known) {
    const word = currentWordData.value;
    wordResults.value.push({ word, known });

    if (known) {
      word.markKnown();
    } else {
      word.markUnknown();
    }

    if (!word.isReady && !reviewQueue.value.includes(word.id)) {
      reviewQueue.value.push(word.id);
    }
  }

  async function getWordData() {
    try {
      const list = await apiService.fetchWords();
      if (!list?.length) return;
      wordsData.value = list.map((raw) => new Word(raw));
      totalLearningCount.value = list.length;
      currentWordData.value = wordsData.value[0];
      currentWordIndex.value = 0;
      progress.value = 0;
    } catch (err) {
      console.error("获取单词失败:", err);
    }
  }

  async function fetchNotes() {
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
  }

  function syncProgress() {
    const payload = buildSyncPayload(wordsData.value, learningStartTime.value);
    apiService.sync(payload).catch((err) => console.error("同步失败:", err));
  }

  function proceedToNext() {
    const studiedCount = wordResults.value.length;
    const next = getNextWord(
      wordsData.value,
      currentWordIndex.value + 1,
      reviewQueue.value,
      studiedCount,
    );

    if (!next) {
      syncProgress();
      appState.value = "summary";
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
  }

  // ====== 外部可调用方法 ======

  async function startLearning() {
    appState.value = "learning";
    learningStartTime.value = Date.now();
    reviewQueue.value = [];
    wordResults.value = [];
    await getWordData();
  }

  async function handleKnown() {
    recordResult(true);
    appState.value = "detail";
    await fetchNotes();
  }

  async function handleUnknown() {
    recordResult(false);
    appState.value = "detail";
    await fetchNotes();
  }

  function handleNext() {
    if (shouldShowSummary.value) {
      syncProgress();
      appState.value = "summary";
      return;
    }
    proceedToNext();
  }

  function continueFromSummary() {
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
  }

  async function viewWordDetail(result) {
    currentWordData.value = result.word;
    appState.value = "detail";
    notes.value = [];
    hasMoreNotes.value = true;
    await fetchNotes();
  }

  // ====== 拼写方法（桥接） ======
  function handleSpellingKeydown(e) {
    rawOnSpellingKeydown(e, currentWordData.value);
  }

  // ====== 键盘路由 ======
  function handleKeyDown(e) {
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
          enterSpellingMode();
        } else if (e.key === "Escape" && spellingMode.value) {
          e.preventDefault();
          exitSpellingMode();
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
  }

  // ====== 生命周期 ======
  onMounted(() => window.addEventListener("keydown", handleKeyDown));
  onUnmounted(() => window.removeEventListener("keydown", handleKeyDown));

  // ====== 返回值 ======
  return {
    // 状态
    appState,
    currentWordData,
    currentWordIndex,
    wordsData,
    notes,
    notesLoading,
    hasMoreNotes,
    wordResults,
    reviewQueue,
    totalLearningCount,
    userInput,
    debugMode,
    debugCode,
    notesContainerRef,

    // 子 composable 状态（模板需要）
    spellingMode,
    isCorrect,
    spellingChars,
    spellingInputRef,
    ukAudioRef,
    usAudioRef,

    // 计算属性
    groupedSenses,
    progressPercent,
    currentBatch,
    debugWordInfo,
    shouldShowSummary,

    // 方法
    startLearning,
    handleKnown,
    handleUnknown,
    handleNext,
    continueFromSummary,
    viewWordDetail,
    playAudio,
    onSpellingKeydown: handleSpellingKeydown,
  };
}
