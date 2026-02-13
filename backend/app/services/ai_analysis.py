import re
import json
import logging
import os

logger = logging.getLogger(__name__)

# Lazy imports to reduce baseline memory
# snownlp, groq, google-genai are imported on first use
from app.services.parser import Message
from app.services.text_analysis import STOP_WORDS

_groq_client = None
_gemini_client = None

_NOISE_RE = re.compile(r"^[\d\W\s]+$|^(.)\1+$")


def _compute_base_score(
    basic_stats: dict | None,
    reply_behavior: dict | None,
    cold_wars: list | None,
) -> tuple[int, dict[str, int]]:
    """Compute a 0-100 base score from quantitative data.

    Returns (base_score, dimensions_dict) where dimensions_dict contains
    per-dimension scores for transparency in the AI prompt.
    """
    # ── 1. 互動頻率 (25%) ──
    freq_score = 50
    if basic_stats:
        mc = basic_stats.get("messageCount", {})
        total_msgs = mc.get("total", 0)
        dr = basic_stats.get("dateRange", {})
        total_days = max(dr.get("totalDays", 1), 1)
        msgs_per_day = total_msgs / total_days

        # Score curve: 0→20, 5→40, 15→60, 30→75, 60→90, 100+→95
        if msgs_per_day >= 100:
            freq_score = 95
        elif msgs_per_day >= 60:
            freq_score = 90
        elif msgs_per_day >= 30:
            freq_score = 75 + (msgs_per_day - 30) / 30 * 15
        elif msgs_per_day >= 15:
            freq_score = 60 + (msgs_per_day - 15) / 15 * 15
        elif msgs_per_day >= 5:
            freq_score = 40 + (msgs_per_day - 5) / 10 * 20
        else:
            freq_score = 20 + msgs_per_day / 5 * 20

        # Call bonus
        cs = basic_stats.get("callStats", {})
        if cs.get("completedCalls", 0) > 0:
            freq_score = min(100, freq_score + 5)

    # ── 2. 主動平衡 (20%) ──
    balance_score = 50
    if basic_stats:
        mc = basic_stats.get("messageCount", {})
        person_counts = [v for k, v in mc.items() if k != "total" and isinstance(v, int)]
        if len(person_counts) >= 2:
            mn, mx = min(person_counts), max(person_counts)
            if mx > 0:
                balance_score = round(mn / mx * 100)

    # ── 3. 回覆默契 (25%) ──
    reply_score = 50
    if reply_behavior:
        irr = reply_behavior.get("instantReplyRate", {})
        lor = reply_behavior.get("leftOnRead", {})

        # Average instant reply rate across persons
        rates = [v for v in irr.values() if isinstance(v, (int, float))]
        avg_irr = sum(rates) / len(rates) * 100 if rates else 50

        # Left-on-read penalty: each occurrence -3, capped at -30
        total_lor = sum(v for v in lor.values() if isinstance(v, int))
        lor_penalty = min(total_lor * 3, 30)

        reply_score = max(0, min(100, round(avg_irr - lor_penalty)))

    # ── 4. 穩定度 (15%) ──
    cw_count = len(cold_wars) if cold_wars else 0
    if cw_count == 0:
        stability_score = 95
    elif cw_count == 1:
        stability_score = 75
    elif cw_count == 2:
        stability_score = 60
    else:
        stability_score = 45

    # ── 5. 聯繫深度 (15%) ──
    depth_score = 50
    if basic_stats:
        cs = basic_stats.get("callStats", {})
        total_call_min = cs.get("totalDurationSeconds", 0) / 60
        # Call minutes bonus: +1 per 5 min, cap +25
        call_bonus = min(round(total_call_min / 5), 25)

        # Longest streak bonus (from dateRange or basic stats)
        # Use total days as proxy for commitment duration
        dr = basic_stats.get("dateRange", {})
        total_days = dr.get("totalDays", 0)
        streak_bonus = min(round(total_days / 10), 25)

        depth_score = min(100, 50 + call_bonus + streak_bonus)

    dimensions = {
        "互動頻率": round(freq_score),
        "主動平衡": round(balance_score),
        "回覆默契": round(reply_score),
        "穩定度": stability_score,
        "聯繫深度": round(depth_score),
    }

    base = round(
        freq_score * 0.25
        + balance_score * 0.20
        + reply_score * 0.25
        + stability_score * 0.15
        + depth_score * 0.15
    )
    base = max(0, min(100, base))

    return base, dimensions


def _is_meaningful(content: str) -> bool:
    """Check if a message has real content worth sending to AI.

    Uses text length and word-level filtering. Messages with ≥3 Chinese
    characters that aren't pure noise are considered meaningful, even if
    individual words are common (e.g. "我好想你喔" is meaningful).
    """
    text = content.strip()
    if len(text) <= 1:
        return False
    if _NOISE_RE.match(text):
        return False

    # Messages with enough Chinese characters are likely meaningful
    cjk_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    if cjk_chars >= 3:
        return True

    # For short/mixed messages, check for substantive words
    from app.services.segmenter import cut
    words = cut(text)
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
        from snownlp import SnowNLP
        score = SnowNLP(content).sentiments
        return abs(score - 0.5)
    except Exception:
        return 0.0


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import AsyncGroq
        _groq_client = AsyncGroq()
    return _groq_client


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return None
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def _message_tfidf_score(words: list[str], word_idf: dict[str, float]) -> float:
    """Sum of IDF scores for non-stop words in a message."""
    return sum(word_idf.get(w, 0) for w in words if len(w) >= 2 and w not in STOP_WORDS)


def sample_messages(
    messages: list[Message],
    msg_words: list[list[str]] | None = None,
    word_idf: dict[str, float] | None = None,
    max_tfidf: int = 1500,
    max_final: int = 800,
) -> list[Message]:
    """Two-stage sampling: TF-IDF top content → SnowNLP top sentiment.

    1. Filter meaningful messages
    2. Score by TF-IDF (sum of word IDF scores) → keep top max_tfidf
    3. Score by SnowNLP sentiment intensity → keep top max_final
    4. Re-sort chronologically for AI
    """
    if not messages:
        return []

    # Phase 1: filter meaningful messages, pair with word lists
    if msg_words and len(msg_words) == len(messages):
        meaningful = [
            (m, words) for m, words in zip(messages, msg_words)
            if m.msg_type == "text" and _is_meaningful(m.content)
        ]
    else:
        meaningful = [
            (m, []) for m in messages
            if m.msg_type == "text" and _is_meaningful(m.content)
        ]

    logger.info("sample_messages: %d total → %d meaningful", len(messages), len(meaningful))

    # Phase 2: if within budget, return all
    if len(meaningful) <= max_final:
        return [m for m, _ in meaningful]

    # Phase 3: TF-IDF score → top max_tfidf
    if word_idf and len(meaningful) > max_tfidf:
        scored = [(m, _message_tfidf_score(words, word_idf)) for m, words in meaningful]
        scored.sort(key=lambda x: x[1], reverse=True)
        tfidf_selected = [(m, s) for m, s in scored[:max_tfidf]]
        logger.info("sample_messages: TF-IDF %d → %d", len(meaningful), len(tfidf_selected))
    else:
        tfidf_selected = [(m, 0) for m, _ in meaningful]

    # Phase 4: SnowNLP sentiment intensity → top max_final
    sentiment_scored = [(m, _sentiment_intensity(m.content)) for m, _ in tfidf_selected]
    sentiment_scored.sort(key=lambda x: x[1], reverse=True)
    final = [m for m, _ in sentiment_scored[:max_final]]
    logger.info("sample_messages: SnowNLP → %d final", len(final))

    # Phase 5: re-sort chronologically
    final.sort(key=lambda m: m.timestamp)
    return final


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

    if "textAnalysis" in stats:
        ta = stats["textAnalysis"]
        wc = ta.get("wordCloud", {})
        if wc:
            lines.append("")
            lines.append("── 雙方高頻詞（已去除停用詞，含出現次數）──")
            for person, words in wc.items():
                top = words[:30]
                if top:
                    items = ", ".join(f"{w['word']}({w['count']})" for w in top)
                    lines.append(f"{person}：{items}")

    return chr(10).join(lines)


def build_prompt(
    messages: list[Message], persons: list[str],
    stats: dict | None = None, interest_context: str = "",
    base_score: int | None = None, dimensions: dict[str, int] | None = None,
) -> str:
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

    # Base score block for AI prompt
    if base_score is not None and dimensions:
        lo = max(base_score - 15, 0)
        hi = min(base_score + 15, 100)
        dim_parts = "  ".join(f"{k}：{v}" for k, v in dimensions.items())
        base_score_block = (
            f"\n── 量化基底分：{base_score} / 100 ──\n"
            f"  {dim_parts}\n"
            f"你的最終 loveScore.score 必須在 {lo}~{hi} 之間（基底分 ±15）。\n"
            f"只有在對話情感品質明顯偏離數據時才大幅調整。\n"
        )
    else:
        base_score_block = ""

    # Interest context block (TF-IDF distinctive words + example sentences)
    interest_block = f"\n\n{interest_context}\n" if interest_context else ""

    return f"""你是一位超級懂感情的閨蜜分析師，說話活潑、帶點俏皮，擅長從聊天記錄中看出兩個人之間的微妙互動和化學反應。

以下是 {p1} 和 {p2} 的聊天記錄。

⚠️ 關係判斷要求（非常重要，請仔細分析後再下結論）：
兩人可能是任何關係——同事、朋友、網友、曖昧對象、情侶、老夫老妻。不要因為對話中日常瑣事多就直接假設是「老夫老妻」或「穩定交往」。請根據以下線索綜合判斷：
- 稱呼方式：用「寶貝/親愛的/老公老婆」vs「學長/同事名」vs「你」差異很大
- 話題邊界：情侶會聊私密心事、撒嬌吃醋；同事朋友主要聊工作、共同話題
- 肢體語言暗示：有沒有「抱抱/親親/想你」等親密表達
- 互動頻率與時段：深夜聊天、每天早晚問候 vs 只在上班時間聊
- 情感濃度：有沒有明顯的曖昧、吃醋、想念、心疼等情緒

判斷出關係階段後，評分和建議都要符合該階段的合理期待。例如：
- 同事/朋友：不需要有甜蜜訊息，重點看互動品質和默契
- 曖昧中：看試探、放電、主動程度
- 穩定交往：看日常關心、衝突處理、情感維繫
- 老夫老妻：日常瑣事多但仍有關心是正常的，不扣分

注意：評分時請同時參考下方的量化數據，例如秒回率高代表主動性強、已讀不回多代表可能有冷淡傾向、通話頻繁代表感情較親密。

{stats_block}
{base_score_block}
── {p1} 說的話 ──
{chr(10).join(p1_lines[-80:])}

── {p2} 說的話 ──
{chr(10).join(p2_lines[-80:])}

── 完整對話時間軸（看互動節奏）──
{chr(10).join(timeline[-120:])}
{interest_block}
⚠️ sharedInterests 填寫規則（非常重要）：
items 必須是對話中出現的【具體專有名詞】，不要寫模糊的類別詞。
✅ 正確範例：寄生上流、黑暗榮耀、鬼滅之刃、周杰倫、五月天、晴天、鼎泰豐、九份、北投溫泉、星巴克、小美（朋友暱稱）
❌ 錯誤範例：韓劇、電影、音樂、散步、健身、甜點（這些是類別詞不是具體名稱，絕對不要寫）
如果對話中沒提到某類別的具體名稱，該類別就不要列出。
共同朋友：對話中頻繁提到的第三人名字或暱稱可作為一個類別。

請綜合以上內容，回傳以下 JSON（不要加 markdown code block、不要加任何其他文字）：
{{
  "loveScore": {{
    "score": <0-100 心動指數。系統已根據量化數據算出基底分（見上方），你的分數必須在基底分 ±15 範圍內。請根據對話的情感品質微調：甜蜜互動多可加分，冷淡敷衍可扣分>,
    "comment": "<80-120 字的活潑評語，2-3 句話。像閨蜜在旁邊幫你分析，第一句點出你們的互動特色或亮點，第二句具體描述一個讓人印象深刻的互動模式，第三句給出一句暖心或俏皮的總結。根據關係階段給出不同風格的點評（曖昧期可以俏皮，老夫老妻可以溫馨）>"
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
  "relationshipType": "<用一個詞描述你判斷的關係類型：同事、朋友、網友、曖昧中、熱戀期、穩定交往、老夫老妻>",
  "insight": "<100 字以內，用活潑的語氣描述 {p1} 和 {p2} 的關係階段和互動模式。先明確點出你判斷的關係類型和依據，再描述互動特色。朋友/同事就分析默契和互動品質；曖昧期分析誰在追誰；情侶分析感情濃度>",
  "sharedInterests": [
    {{
      "category": "<愛去的地方 / 愛吃的東西 / 愛看的劇 / 愛聽的音樂 / 常一起做的事 / 共同朋友 / 或自訂>",
      "items": [{{"name": "<具體專有名詞>"}}, {{"name": "..."}}]
    }}
  ],
  "advice": [
    {{"category": "💬 聊天技巧", "target": "{p1}", "content": "<根據 {p1} 的聊天風格，給一句具體、可執行的溝通建議，例如回覆速度、表達方式、主動程度等>"}},
    {{"category": "💬 聊天技巧", "target": "{p2}", "content": "<根據 {p2} 的聊天風格，給一句具體、可執行的溝通建議>"}},
    {{"category": "❤️ 感情增溫", "target": "兩人", "content": "<一個具體的互動建議，例如可以嘗試的話題、小遊戲、或讓對話更有溫度的方法>"}},
    {{"category": "🎯 約會靈感", "target": "兩人", "content": "<根據對話中提到的地點、食物、興趣，推薦一個具體的約會或活動點子>"}},
    {{"category": "⚡ 默契升級", "target": "兩人", "content": "<針對目前互動模式中可以改善的地方，例如回覆節奏不同步、話題深度不夠、或某方太被動等，給出具體建議>"}},
    {{"category": "🌟 關係成長", "target": "兩人", "content": "<根據判斷出的關係階段，給一個幫助關係進階的建議。曖昧期：怎麼更明確表達心意；穩定期：怎麼保持新鮮感；老夫老妻：怎麼重新找回心動>"}}
  ]
}}"""


class AIRateLimitError(Exception):
    """Raised when all AI providers are rate limited."""
    pass


def _parse_ai_response(text: str, provider: str) -> dict | None:
    """Parse AI response text into dict. Returns None on failure."""
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    if "```" in text:
        try:
            json_str = text.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            pass

    logger.error("[%s] JSON parse failed, text preview: %s", provider, text[:500])
    return None


async def _call_groq(prompt: str) -> dict | None:
    """Try Groq API. Returns parsed dict, None on parse failure, raises on rate limit."""
    client = _get_groq_client()

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=3000,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e).lower():
            logger.warning("[Groq] Rate limited: %s", e)
            return None  # Signal to try fallback
        raise

    text = response.choices[0].message.content.strip()
    finish_reason = response.choices[0].finish_reason

    if finish_reason != "stop":
        logger.warning("[Groq] Response truncated (finish_reason=%s), length=%d", finish_reason, len(text))

    result = _parse_ai_response(text, "Groq")
    if result:
        logger.info("[Groq] AI analysis succeeded")
    return result


async def _call_gemini(prompt: str) -> dict | None:
    """Try Google Gemini API as fallback."""
    client = _get_gemini_client()
    if client is None:
        logger.warning("[Gemini] No GOOGLE_API_KEY configured, skipping")
        return None

    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
    except Exception as e:
        if "429" in str(e) or "rate" in str(e).lower():
            logger.warning("[Gemini] Rate limited: %s", e)
            return None
        logger.exception("[Gemini] API call failed")
        return None

    text = response.text or ""

    result = _parse_ai_response(text, "Gemini")
    if result:
        logger.info("[Gemini] AI analysis succeeded (fallback)")
    return result


def _clamp_love_score(ai_result: dict, base_score: int | None) -> None:
    """Clamp AI loveScore to [base-15, base+15] range."""
    if base_score is None:
        return
    ls = ai_result.get("loveScore")
    if not ls or "score" not in ls:
        return
    score = ls["score"]
    if not isinstance(score, (int, float)):
        return
    lo = max(base_score - 15, 0)
    hi = min(base_score + 15, 100)
    ls["score"] = max(lo, min(hi, int(score)))


async def analyze_with_ai(
    messages: list[Message], persons: list[str], stats: dict | None = None,
    interest_context: str = "",
    msg_words: list[list[str]] | None = None,
    word_idf: dict[str, float] | None = None,
    base_score: int | None = None,
    dimensions: dict[str, int] | None = None,
) -> dict:
    """Call AI API with Groq → Gemini fallback chain."""
    sampled = sample_messages(messages, msg_words=msg_words, word_idf=word_idf)
    if not sampled:
        return _fallback_result()

    prompt = build_prompt(
        sampled, persons, stats, interest_context=interest_context,
        base_score=base_score, dimensions=dimensions,
    )

    # 1. Try Groq (faster)
    result = await _call_groq(prompt)
    if result:
        _clamp_love_score(result, base_score)
        return result

    # 2. Fallback to Gemini
    logger.info("Groq unavailable, falling back to Gemini")
    result = await _call_gemini(prompt)
    if result:
        _clamp_love_score(result, base_score)
        return result

    # 3. Both failed
    logger.error("All AI providers failed")
    raise AIRateLimitError("AI 分析服務暫時不可用，請稍後再試")


def _fallback_result() -> dict:
    return {
        "loveScore": {"score": 50, "comment": "資料不足，無法完整分析"},
        "sentiment": {"sweet": 20, "flirty": 20, "daily": 40, "conflict": 10, "missing": 10},
        "goldenQuotes": {"sweetest": [], "funniest": [], "mostTouching": []},
        "insight": "對話內容不足，建議上傳更長的對話記錄以獲得更準確的分析。",
        "advice": [],
    }
