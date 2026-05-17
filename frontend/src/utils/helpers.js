/**
 * 构建同步到后端的 payload
 */
export function buildSyncPayload(words, startTime) {
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

/**
 * 根据队列和原始单词表，返回下一个要学习的词（或 null）
 * 规则：批次边界（每 7 个）且队列非空时优先队列；否则返回 words[nextRawIndex]
 */
export function getNextWord(words, rawIndex, queue, learnedCount) {
  if (learnedCount > 0 && learnedCount % 7 === 0 && queue.length > 0) {
    const id = queue[0];
    const found = words.find((w) => w.id === id);
    if (found) return { word: found, type: "review" };
  }
  if (rawIndex < words.length) {
    return { word: words[rawIndex], type: "new" };
  }
  if (queue.length > 0) {
    const id = queue[0];
    const found = words.find((w) => w.id === id);
    if (found) return { word: found, type: "review" };
  }
  return null;
}

/**
 * 拼写键盘输入处理（纯函数）
 */
export function handleSpellingKey(e, charArray, wordLen) {
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
}
