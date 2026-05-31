/**
 * Word 数据模型
 */
export class Word {
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
