import json
import os
from collections import defaultdict
from datetime import datetime

from app.services.parser import Message

# Lazy import anthropic to allow tests without API key
_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.AsyncAnthropic()
    return _client


def sample_messages(
    messages: list[Message], per_day: int = 8
) -> list[Message]:
    """Sample representative messages per day to reduce API cost."""
    if not messages:
        return []

    by_day: dict[str, list[Message]] = defaultdict(list)
    for m in messages:
        if m.msg_type == "text":
            by_day[str(m.timestamp.date())].append(m)

    sampled = []
    for day in sorted(by_day):
        day_msgs = by_day[day]
        if len(day_msgs) <= per_day:
            sampled.extend(day_msgs)
        else:
            step = len(day_msgs) / per_day
            sampled.extend(day_msgs[int(i * step)] for i in range(per_day))

    return sampled


def build_prompt(messages: list[Message], persons: list[str]) -> str:
    lines = []
    for m in messages:
        lines.append(f"[{m.timestamp.strftime('%Y-%m-%d %H:%M')}] {m.sender}: {m.content}")

    conversation = "\n".join(lines)
    p1, p2 = persons[0], persons[1] if len(persons) > 1 else "Person2"

    return f"""你是一位專業的聊天對話分析師。請分析以下 {p1} 和 {p2} 之間的對話摘錄，回傳 JSON 格式結果。

對話摘錄：
{conversation}

請回傳以下 JSON（不要加 markdown code block）：
{{
  "loveScore": {{
    "score": <0-100 的整數，代表兩人的心動/互動指數>,
    "comment": "<一段 50 字以內的中文整體評語>"
  }},
  "sentiment": {{
    "sweet": <甜蜜訊息佔比 0-100>,
    "flirty": <曖昧/調情佔比 0-100>,
    "daily": <日常分享佔比 0-100>,
    "conflict": <爭吵/不滿佔比 0-100>,
    "missing": <思念佔比 0-100>
  }},
  "goldenQuotes": {{
    "sweetest": [
      {{"quote": "<原文>", "sender": "<發送者>", "date": "<日期>"}},
    ],
    "funniest": [
      {{"quote": "<原文>", "sender": "<發送者>", "date": "<日期>"}}
    ],
    "mostTouching": [
      {{"quote": "<原文>", "sender": "<發送者>", "date": "<日期>"}}
    ]
  }},
  "insight": "<一段 100 字以內的中文深度洞察，描述兩人的互動模式和關係特色>"
}}"""


async def analyze_with_ai(
    messages: list[Message], persons: list[str]
) -> dict:
    """Call Claude API for sentiment analysis and golden quotes."""
    sampled = sample_messages(messages)
    if not sampled:
        return _fallback_result()

    prompt = build_prompt(sampled, persons)
    client = _get_client()

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    # Try to parse JSON from response
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
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
    }
