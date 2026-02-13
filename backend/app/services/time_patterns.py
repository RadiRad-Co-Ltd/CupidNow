import re
from collections import defaultdict
from datetime import datetime
from app.services.parser import Message


# Use word boundaries (\b) to avoid matching inside URLs or other words
GOODNIGHT_RE = re.compile(r"(晚安|good\s*night\b|睡了|想睡|睡覺)", re.IGNORECASE)
GOODMORNING_RE = re.compile(r"(早安|早～|早啊|good\s*morning\b|起床了)", re.IGNORECASE)
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def compute_time_patterns(parsed: dict) -> dict:
    messages: list[Message] = parsed["messages"]
    persons: list[str] = parsed["persons"]

    heatmap = _build_heatmap(messages)
    trend = _build_trend(messages, persons)
    goodnight = _build_goodnight(messages, persons)

    return {
        "heatmap": heatmap,
        "trend": trend,
        "goodnightAnalysis": goodnight,
    }


def _build_heatmap(messages: list[Message]) -> list[list[int]]:
    """7 rows (Mon=0..Sun=6) x 24 cols (0-23, one per hour)."""
    grid = [[0] * 24 for _ in range(7)]
    for m in messages:
        day = m.timestamp.weekday()  # 0=Mon
        grid[day][m.timestamp.hour] += 1
    return grid


def _build_trend(messages: list[Message], persons: list[str]) -> list[dict]:
    """Daily message counts per person (YYYY-MM-DD)."""
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {p: 0 for p in persons})
    for m in messages:
        key = str(m.timestamp.date())  # "2024-03-15"
        buckets[key][m.sender] += 1

    result = []
    for period in sorted(buckets):
        entry = {"period": period, **buckets[period]}
        result.append(entry)
    return result


def _is_greeting(content: str, pattern: re.Pattern) -> bool:
    """Check if message matches greeting pattern, ignoring URLs."""
    text = _URL_RE.sub("", content)
    return bool(pattern.search(text))


def _build_goodnight(messages: list[Message], persons: list[str]) -> dict:
    gn_first: dict[str, int] = defaultdict(int)
    gm_first: dict[str, int] = defaultdict(int)
    last_chat_hours: list[float] = []
    bedtime_durations: list[float] = []  # in minutes

    # Group messages by date
    by_date: dict[str, list[Message]] = defaultdict(list)
    for m in messages:
        by_date[str(m.timestamp.date())].append(m)

    for date_str, day_msgs in by_date.items():
        # Find first goodnight (only count after 21:00)
        for m in day_msgs:
            if (m.msg_type == "text"
                    and m.timestamp.hour >= 21
                    and _is_greeting(m.content, GOODNIGHT_RE)):
                gn_first[m.sender] += 1
                break

        # Find first good morning (only count between 5:00-11:59)
        for m in day_msgs:
            if (m.msg_type == "text"
                    and 5 <= m.timestamp.hour < 12
                    and _is_greeting(m.content, GOODMORNING_RE)):
                gm_first[m.sender] += 1
                break

        # Last message time of day (only count days with messages after 20:00)
        night_last = [m for m in day_msgs if m.timestamp.hour >= 20]
        if night_last:
            last = night_last[-1].timestamp
            last_chat_hours.append(last.hour + last.minute / 60)

        # Bedtime chat duration: last continuous conversation block after 22:00
        night_msgs = [m for m in day_msgs if m.timestamp.hour >= 22]
        if len(night_msgs) >= 2:
            block_start = night_msgs[-1].timestamp
            for i in range(len(night_msgs) - 1, 0, -1):
                gap = (night_msgs[i].timestamp - night_msgs[i - 1].timestamp).total_seconds()
                if gap > 600:  # 10 min gap = conversation break
                    break
                block_start = night_msgs[i - 1].timestamp
            duration_min = (night_msgs[-1].timestamp - block_start).total_seconds() / 60
            if duration_min >= 1:
                bedtime_durations.append(duration_min)

    avg_last = round(sum(last_chat_hours) / len(last_chat_hours), 1) if last_chat_hours else 0
    avg_bedtime_chat = round(sum(bedtime_durations) / len(bedtime_durations)) if bedtime_durations else 0

    return {
        "whoSaysGoodnightFirst": dict(gn_first),
        "whoSaysGoodmorningFirst": dict(gm_first),
        "avgLastChatTime": avg_last,
        "avgBedtimeChatMinutes": avg_bedtime_chat,
        "bedtimeChatCount": len(bedtime_durations),
    }
