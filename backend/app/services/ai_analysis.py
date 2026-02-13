import re
import json
import os
from collections import defaultdict

import jieba
from snownlp import SnowNLP
from app.services.parser import Message
from app.services.text_analysis import STOP_WORDS

_client = None

_NOISE_RE = re.compile(r"^[\d\W\s]+$|^(.)\1+$")


def _is_meaningful(content: str) -> bool:
    """Use jieba + STOP_WORDS to check if a message has real content.

    Segment the message, strip stop words / punctuation / numbers.
    If nothing remains → trivial message, not worth sending to AI.
    """
    text = content.strip()
    if len(text) <= 1:
        return False
    if _NOISE_RE.match(text):
        return False

    words = jieba.lcut(text)
    substantive = [
        w for w in words
        if len(w) >= 2
        and w not in STOP_WORDS
        and not re.match(r"^[\d\W]+$", w)
        and not re.match(r"^(.)\1+$", w)
    ]
    return len(substantive) >= 1


def _sentiment_intensity(content: str) -> float:
    """Return 0~0.5: how emotionally charged this message is.

    SnowNLP returns 0 (negative) ~ 1 (positive).
    Intensity = distance from neutral (0.5).
    Strong positive (0.95) → 0.45, strong negative (0.05) → 0.45
    Neutral (0.50) → 0.0
    """
    try:
        score = SnowNLP(content).sentiments
        return abs(score - 0.5)
    except Exception:
        return 0.0


def _get_client():
    global _client
    if _client is None:
        from groq import AsyncGroq
        _client = AsyncGroq()
    return _client


def sample_messages(
    messages: list[Message], max_total: int = 500
) -> list[Message]:
    """Filter out trivial messages, then prioritize by sentiment intensity."""
    if not messages:
        return []

    # Phase 1: jieba + STOP_WORDS — remove noise
    meaningful = [
        m for m in messages
        if m.msg_type == "text" and _is_meaningful(m.content)
    ]

    # Phase 2: if within budget, return all
    if len(meaningful) <= max_total:
        return meaningful

    # Phase 3: score each message by SnowNLP sentiment intensity,
    # keep the most emotionally charged ones
    scored = [(m, _sentiment_intensity(m.content)) for m in meaningful]
    scored.sort(key=lambda x: x[1], reverse=True)
    selected = [m for m, _ in scored[:max_total]]

    # Re-sort by timestamp so the AI sees messages in chronological order
    selected.sort(key=lambda m: m.timestamp)
    return selected


def build_prompt(messages: list[Message], persons: list[str]) -> str:
    p1 = persons[0]
    p2 = persons[1] if len(persons) > 1 else "Person2"

    # Split messages by person for context
    p1_lines, p2_lines = [], []
    for m in messages:
        content = m.content[:80] if len(m.content) > 80 else m.content
        line = f"[{m.timestamp.strftime('%m/%d %H:%M')}] {content}"
        if m.sender == p1:
            p1_lines.append(line)
        else:
            p2_lines.append(line)

    # Also build interleaved timeline for context
    timeline = []
    for m in messages:
        content = m.content[:80] if len(m.content) > 80 else m.content
        timeline.append(f"[{m.timestamp.strftime('%m/%d %H:%M')}] {m.sender}: {content}")

    return f"""你是一位超級懂感情的閨蜜分析師，說話活潑、帶點俏皮，擅長從聊天記錄中看出兩個人之間的微妙互動和化學反應。

以下是 {p1} 和 {p2} 的聊天記錄。他們可能是情侶、曖昧中、剛認識、或是好朋友，請你從對話內容自行判斷兩人目前的關係階段，再給出分析。

── {p1} 說的話 ──
{chr(10).join(p1_lines[-80:])}

── {p2} 說的話 ──
{chr(10).join(p2_lines[-80:])}

── 完整對話時間軸（看互動節奏）──
{chr(10).join(timeline[-120:])}

請綜合以上內容，回傳以下 JSON（不要加 markdown code block、不要加任何其他文字）：
{{
  "loveScore": {{
    "score": <0-100 心動指數，請參考以下五個維度綜合評分，但你也可以根據對話特色自行調整權重：
      甜度/撒嬌頻率（約 25%）：甜蜜訊息的佔比和濃度
      主動性平衡（約 20%）：雙方主動發訊的比例是否均衡，還是單方面在追
      曖昧/放電（約 20%）：調情、試探、暗示、撩的頻率和程度
      默契度（約 20%）：回覆速度、話題銜接順暢度、互相呼應的程度
      衝突修復力（約 15%）：吵架或冷淡後多快回溫、有沒有主動破冰
    >,
    "comment": "<50 字以內的活潑評語，像閨蜜在旁邊幫你分析對方的語氣，根據關係階段給出不同風格的點評>"
  }},
  "sentiment": {{
    "sweet": <甜蜜撒嬌佔比 0-100>,
    "flirty": <曖昧放電、試探、調情佔比 0-100>,
    "daily": <柴米油鹽日常佔比 0-100>,
    "conflict": <火藥味、冷淡、不耐煩佔比 0-100>,
    "missing": <想念、捨不得、在意對方佔比 0-100>
  }},
  "goldenQuotes": {{
    "sweetest": [
      {{"quote": "<原文>", "sender": "<誰說的>", "date": "<幾月/幾日>"}},
      {{"quote": "<原文>", "sender": "<誰說的>", "date": "<幾月/幾日>"}},
      {{"quote": "<原文>", "sender": "<誰說的>", "date": "<幾月/幾日>"}}
    ],
    "funniest": [
      {{"quote": "<原文>", "sender": "<誰說的>", "date": "<幾月/幾日>"}},
      {{"quote": "<原文>", "sender": "<誰說的>", "date": "<幾月/幾日>"}},
      {{"quote": "<原文>", "sender": "<誰說的>", "date": "<幾月/幾日>"}}
    ],
    "mostTouching": [
      {{"quote": "<原文>", "sender": "<誰說的>", "date": "<幾月/幾日>"}},
      {{"quote": "<原文>", "sender": "<誰說的>", "date": "<幾月/幾日>"}},
      {{"quote": "<原文>", "sender": "<誰說的>", "date": "<幾月/幾日>"}}
    ]
  }},
  "insight": "<100 字以內，用活潑的語氣描述 {p1} 和 {p2} 的關係階段和互動模式，例如誰比較主動、誰在等對方出招、曖昧濃度有多高、有沒有什麼讓人心動的小細節>",
  "advice": [
    "<一句具體的聊天建議，針對 {p1}，可以是正面鼓勵也可以是善意提醒，例如回覆太慢、太已讀不回、話題太乾、或是某個做得很好的地方>",
    "<一句具體的聊天建議，針對 {p2}，同上>",
    "<一句針對兩人互動的整體建議，例如聊天節奏、話題深度、主動性落差、或是可以嘗試的互動方式>"
  ]
}}"""


async def analyze_with_ai(
    messages: list[Message], persons: list[str]
) -> dict:
    """Call Groq API for sentiment analysis and golden quotes."""
    sampled = sample_messages(messages)
    if not sampled:
        return _fallback_result()

    prompt = build_prompt(sampled, persons)
    client = _get_client()

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2000,
        temperature=0.5,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.choices[0].message.content.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if "```" in text:
            json_str = text.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            return json.loads(json_str.strip())
        return _fallback_result()


def _fallback_result() -> dict:
    return {
        "loveScore": {"score": 50, "comment": "資料不足，無法完整分析"},
        "sentiment": {"sweet": 20, "flirty": 20, "daily": 40, "conflict": 10, "missing": 10},
        "goldenQuotes": {"sweetest": [], "funniest": [], "mostTouching": []},
        "insight": "對話內容不足，建議上傳更長的對話記錄以獲得更準確的分析。",
        "advice": [],
    }
