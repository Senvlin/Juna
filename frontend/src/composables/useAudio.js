import { ref } from "vue";

/**
 * 音频播放 composable
 */
export function useAudio() {
  const ukAudioRef = ref(null);
  const usAudioRef = ref(null);

  function playAudio(type) {
    const refEl = type === "uk" ? ukAudioRef : usAudioRef;
    if (!refEl.value) return;
    refEl.value.currentTime = 0;
    refEl.value.play().catch(() => {});
  }

  return {
    ukAudioRef,
    usAudioRef,
    playAudio,
  };
}
