import re
from collections import defaultdict
from datetime import datetime
from app.services.parser import Message


GOODNIGHT_RE = re.compile(r"(晚安|good\s*night|gn|拜拜|掰掰|睡了|想睡)", re.IGNORECASE)
GOODMORNING_RE = re.compile(r"(早安|早～|早啊|good\s*morning|gm|起床)", re.IGNORECASE)


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
    """7 rows (Mon=0..Sun=6) x 8 cols (0-3, 3-6, ..., 21-24)"""
    grid = [[0] * 8 for _ in range(7)]
    for m in messages:
        day = m.timestamp.weekday()  # 0=Mon
        slot = m.timestamp.hour // 3  # 0-7
        grid[day][slot] += 1
    return grid


def _build_trend(messages: list[Message], persons: list[str]) -> list[dict]:
    """Monthly message counts per person."""
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {p: 0 for p in persons})
    for m in messages:
        key = m.timestamp.strftime("%Y-%m")
        buckets[key][m.sender] += 1

    result = []
    for period in sorted(buckets):
        entry = {"period": period, **buckets[period]}
        result.append(entry)
    return result


def _build_goodnight(messages: list[Message], persons: list[str]) -> dict:
    gn_first: dict[str, int] = defaultdict(int)
    gm_first: dict[str, int] = defaultdict(int)
    last_chat_hours: list[float] = []

    # Group messages by date
    by_date: dict[str, list[Message]] = defaultdict(list)
    for m in messages:
        by_date[str(m.timestamp.date())].append(m)

    for date_str, day_msgs in by_date.items():
        # Find first goodnight
        for m in day_msgs:
            if m.msg_type == "text" and GOODNIGHT_RE.search(m.content):
                gn_first[m.sender] += 1
                break

        # Find first good morning
        for m in day_msgs:
            if m.msg_type == "text" and GOODMORNING_RE.search(m.content):
                gm_first[m.sender] += 1
                break

        # Last message time of day
        if day_msgs:
            last = day_msgs[-1].timestamp
            last_chat_hours.append(last.hour + last.minute / 60)

    avg_last = round(sum(last_chat_hours) / len(last_chat_hours), 1) if last_chat_hours else 0

    return {
        "whoSaysGoodnightFirst": dict(gn_first),
        "whoSaysGoodmorningFirst": dict(gm_first),
        "avgLastChatTime": avg_last,
    }
