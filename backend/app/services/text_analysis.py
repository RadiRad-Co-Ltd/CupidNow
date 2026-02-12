import re
from collections import Counter
from app.services.parser import Message

import jieba

# Common Chinese stop words
STOP_WORDS = {
    "的", "了", "是", "我", "你", "他", "她", "在", "有", "也", "不",
    "就", "都", "好", "嗎", "呢", "吧", "啊", "喔", "哦", "欸",
    "這", "那", "會", "要", "跟", "和", "但", "可以", "什麼", "沒有",
    "一個", "很", "還", "被", "把", "到", "說",
}


def compute_text_analysis(parsed: dict) -> dict:
    messages: list[Message] = parsed["messages"]
    persons: list[str] = parsed["persons"]

    word_cloud = {}
    all_words_by_person: dict[str, Counter] = {}

    for p in persons:
        texts = [m.content for m in messages if m.sender == p and m.msg_type == "text"]
        combined = " ".join(texts)
        words = jieba.lcut(combined)
        # Filter: length >= 2, not stop words, not pure punctuation/numbers
        filtered = [
            w for w in words
            if len(w) >= 2
            and w not in STOP_WORDS
            and not re.match(r"^[\d\W]+$", w)
        ]
        counter = Counter(filtered)
        all_words_by_person[p] = counter
        word_cloud[p] = [
            {"word": w, "count": c}
            for w, c in counter.most_common(80)
        ]

    # Unique phrases: words that appear disproportionately in THIS chat
    # Simple approach: words used by both persons (shared vocabulary)
    if len(persons) == 2:
        p1, p2 = persons
        shared = set(all_words_by_person[p1]) & set(all_words_by_person[p2])
        unique = sorted(
            shared,
            key=lambda w: all_words_by_person[p1][w] + all_words_by_person[p2][w],
            reverse=True,
        )[:20]
        unique_phrases = [
            {
                "phrase": w,
                "count": all_words_by_person[p1][w] + all_words_by_person[p2][w],
            }
            for w in unique
        ]
    else:
        unique_phrases = []

    return {
        "wordCloud": word_cloud,
        "uniquePhrases": unique_phrases,
    }
