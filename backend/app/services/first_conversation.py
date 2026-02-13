"""Extract the first continuous conversation burst from parsed chat data."""

from __future__ import annotations

from datetime import timedelta

from app.services.parser import Message

# Two adjacent messages within this gap are considered part of the same burst.
BURST_GAP = timedelta(minutes=30)
MIN_BURST = 5       # fewer than this → fallback to first N messages
FALLBACK_COUNT = 20  # how many messages to show in fallback mode
MAX_MESSAGES = 50    # hard cap to keep payload small

_NON_TEXT_LABELS: dict[str, str] = {
    "sticker": "[貼圖]",
    "photo": "[照片]",
    "video": "[影片]",
    "file": "[檔案]",
    "link": "[連結]",
    "emoji": "[表情符號]",
}


def _format_message(msg: Message) -> dict:
    content = msg.content
    if msg.msg_type != "text":
        content = _NON_TEXT_LABELS.get(msg.msg_type, content)
    return {
        "timestamp": msg.timestamp.isoformat(),
        "sender": msg.sender,
        "content": content,
        "msgType": msg.msg_type,
    }


def extract_first_conversation(parsed: dict) -> dict | None:
    """Return the first continuous conversation burst.

    Returns ``None`` when *messages* is empty.
    """
    messages: list[Message] = parsed.get("messages", [])
    if not messages:
        return None

    # --- collect the first burst ---
    burst: list[Message] = [messages[0]]
    for prev, cur in zip(messages, messages[1:]):
        if cur.timestamp - prev.timestamp > BURST_GAP:
            break
        burst.append(cur)

    is_fallback = len(burst) < MIN_BURST
    if is_fallback:
        chosen = messages[:FALLBACK_COUNT]
    else:
        chosen = burst

    # Hard cap
    chosen = chosen[:MAX_MESSAGES]

    return {
        "messages": [_format_message(m) for m in chosen],
        "startDate": chosen[0].timestamp.strftime("%Y-%m-%d"),
        "isFallback": is_fallback,
    }
