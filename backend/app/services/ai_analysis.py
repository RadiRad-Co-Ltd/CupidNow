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


def _format_stats_block(stats: dict | None) -> str:
    """Format quantitative stats into a concise block for the AI prompt."""
    if not stats:
        return ""

    lines = ["── 量化數據（供評分參考）──"]

    if "basicStats" in stats:
        bs = stats["basicStats"]
        mc = bs.get("messageCount", {})
        lines.append(f"總訊息數：{mc.get('total', 0):,}")
        persons = [k for k in mc if k != "total"]
        for p in persons:
            lines.append(f"  {p}：{mc.get(p, 0):,} 則")
        dr = bs.get("dateRange", {})
        lines.append(f"聊天天數：{dr.get('totalDays', 0)} 天（{dr.get('start', '')} ~ {dr.get('end', '')}）")
        cs = bs.get("callStats", {})
        if cs.get("totalCalls", 0) > 0:
            avg_min = round(cs.get("avgDurationSeconds", 0) / 60)
            lines.append(f"通話：{cs['completedCalls']} 通，平均 {avg_min} 分鐘")

    if "replyBehavior" in stats:
        rb = stats["replyBehavior"]
        irr = rb.get("instantReplyRate", {})
        for p, rate in irr.items():
            lines.append(f"{p} 秒回率：{round(rate * 100)}%")
        art = rb.get("avgReplyTime", {})
        for p, sec in art.items():
            lines.append(f"{p} 平均回覆時間：{round(sec / 60, 1)} 分鐘")
        lor = rb.get("leftOnRead", {})
        for p, cnt in lor.items():
            lines.append(f"{p} 已讀不回次數：{cnt}")

    if "coldWars" in stats:
        cw = stats["coldWars"]
        if cw:
            lines.append(f"冷戰/低潮期：{len(cw)} 次")
        else:
            lines.append("冷戰/低潮期：0 次")

    return chr(10).join(lines)


def build_prompt(messages: list[Message], persons: list[str], stats: dict | None = None) -> str:
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

    stats_block = _format_stats_block(stats)

    return f"""你是一位超級懂感情的閨蜜分析師，說話活潑、帶點俏皮，擅長從聊天記錄中看出兩個人之間的微妙互動和化學反應。

以下是 {p1} 和 {p2} 的聊天記錄。他們可能處於任何關係階段——剛認識、曖昧中、熱戀期、穩定交往、老夫老妻、甚至只是好朋友。請你從對話內容自行判斷兩人目前的關係階段，再給出分析。

注意：
1. 如果判斷為長期穩定交往或老夫老妻，日常瑣事多、甜度低是正常的，不要因此給低分。但如果連基本的關心和互動都很少，可以給出讓彼此感情加溫的具體建議。
2. sharedInterests 請從對話中挖掘他們聊過的地點、美食、影劇、音樂、共同活動等。只列對話中實際提到的內容，沒提到的類別就省略不要硬湊。每個類別最多列 5 項。
3. 評分時請同時參考下方的量化數據，例如秒回率高代表主動性強、已讀不回多代表可能有冷淡傾向、通話頻繁代表感情較親密。

{stats_block}

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
      甜度/關心頻率（約 25%）：甜蜜訊息的佔比和濃度，長期伴侶的日常關心（吃了嗎、路上小心）也算
      主動性平衡（約 20%）：雙方主動發訊的比例是否均衡，還是單方面在追
      情感表達（約 20%）：曖昧期看調情放電，穩定期看有沒有持續表達愛意和在乎
      默契度（約 20%）：回覆速度、話題銜接順暢度、互相呼應的程度
      衝突修復力（約 15%）：吵架或冷淡後多快回溫、有沒有主動破冰
    >,
    "comment": "<50 字以內的活潑評語，像閨蜜在旁邊幫你分析對方的語氣，根據關係階段給出不同風格的點評（曖昧期可以俏皮，老夫老妻可以溫馨）>"
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
  "insight": "<100 字以內，用活潑的語氣描述 {p1} 和 {p2} 的關係階段和互動模式。曖昧期可以分析誰在追誰、放電濃度；穩定期可以分析默契程度、有沒有陷入公式化聊天>",
  "sharedInterests": [
    {{"category": "<類別名稱，例如：愛去的地方>", "items": ["<項目1>", "<項目2>", "..."]}},
    {{"category": "<類別名稱，例如：愛吃的東西>", "items": ["<項目1>", "<項目2>", "..."]}},
    {{"category": "<類別名稱，例如：愛看的劇/電影>", "items": ["..."]}},
    {{"category": "<類別名稱，例如：愛聽的音樂>", "items": ["..."]}},
    {{"category": "<類別名稱，例如：常一起做的事>", "items": ["..."]}}
  ],
  "advice": [
    "<一句具體的聊天建議，針對 {p1}，可以是正面鼓勵也可以是善意提醒。穩定交往的話可以建議怎麼讓對話更有溫度、製造小驚喜>",
    "<一句具體的聊天建議，針對 {p2}，同上>",
    "<一句針對兩人互動的整體建議。如果是老夫老妻模式，可以建議怎麼打破日常慣性、重新找回心動感>"
  ]
}}"""


async def analyze_with_ai(
    messages: list[Message], persons: list[str], stats: dict | None = None,
) -> dict:
    """Call Groq API for sentiment analysis and golden quotes."""
    sampled = sample_messages(messages)
    if not sampled:
        return _fallback_result()

    prompt = build_prompt(sampled, persons, stats)
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
