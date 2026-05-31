import { ref, nextTick } from "vue";
import { handleSpellingKey } from "../utils/helpers";

/**
 * 拼写模式 composable
 */
export function useSpelling() {
  const spellingMode = ref(false);
  const isCorrect = ref(null);
  const spellingChars = ref([]);
  const spellingInputRef = ref(null);

  function checkSpelling(word) {
    if (!word) return;
    const result = word.checkSpelling(spellingChars.value);
    isCorrect.value = result.isCorrect;

    if (result.isCorrect === true) {
      setTimeout(() => {
        spellingMode.value = false;
        isCorrect.value = null;
        spellingChars.value = [];
      }, 1200);
    } else if (result.isCorrect === false) {
      setTimeout(() => {
        if (spellingChars.value.length >= (word?.length ?? 0)) {
          isCorrect.value = null;
          spellingChars.value = [];
        }
      }, 1200);
    }
  }

  function onSpellingKeydown(e, word) {
    const wordLen = word?.length ?? 0;
    const { action, chars } = handleSpellingKey(
      e,
      spellingChars.value,
      wordLen,
    );

    if (action === "update") {
      isCorrect.value = null;
      spellingChars.value = chars;
      if (chars.length === wordLen) {
        checkSpelling(word);
      }
    } else if (action === "check") {
      checkSpelling(word);
    }
  }

  function enterSpellingMode() {
    spellingMode.value = true;
    spellingChars.value = [];
    isCorrect.value = null;
    nextTick(() => spellingInputRef.value?.focus());
  }

  function exitSpellingMode() {
    spellingMode.value = false;
    isCorrect.value = null;
    spellingChars.value = [];
  }

  function resetSpelling() {
    spellingMode.value = false;
    isCorrect.value = null;
    spellingChars.value = [];
  }

  return {
    spellingMode,
    isCorrect,
    spellingChars,
    spellingInputRef,
    onSpellingKeydown,
    enterSpellingMode,
    exitSpellingMode,
    resetSpelling,
  };
}
