import re
import json
import logging
import os

logger = logging.getLogger(__name__)

# Lazy imports to reduce baseline memory
# jieba, snownlp, groq, google-genai are imported on first use
from app.services.parser import Message
from app.services.text_analysis import STOP_WORDS

_groq_client = None
_gemini_client = None

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

    import jieba
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

    # Phase 3: uniform sampling to reduce to ~2x budget, then score
    # This avoids running SnowNLP on thousands of messages
    import random
    if len(meaningful) > max_total * 3:
        random.seed(42)
        meaningful = random.sample(meaningful, max_total * 3)

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
      "category": "<類別名稱，例如：愛去的地方、愛吃的東西、愛看的劇、愛聽的音樂、常一起做的事、共同的嗜好，或任何你從對話中發現的共同興趣類別>",
      "items": ["<具體名稱1>", "<具體名稱2>", "<具體名稱3>"]
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


async def analyze_with_ai(
    messages: list[Message], persons: list[str], stats: dict | None = None,
) -> dict:
    """Call AI API with Groq → Gemini fallback chain."""
    sampled = sample_messages(messages)
    if not sampled:
        return _fallback_result()

    prompt = build_prompt(sampled, persons, stats)

    # 1. Try Groq (faster)
    result = await _call_groq(prompt)
    if result:
        return result

    # 2. Fallback to Gemini
    logger.info("Groq unavailable, falling back to Gemini")
    result = await _call_gemini(prompt)
    if result:
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
