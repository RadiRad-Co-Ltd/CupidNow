import re
from collections import defaultdict
from datetime import datetime
from app.services.parser import Message


GOODNIGHT_RE = re.compile(r"(晚安|good\s*night|gn|睡了|想睡)", re.IGNORECASE)
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

        # Bedtime chat duration: last continuous conversation block after 23:00
        # Walk backwards from last message, find the last gap > 10 min
        night_msgs = [m for m in day_msgs if m.timestamp.hour >= 23]
        if len(night_msgs) >= 2:
            # Find where the last continuous block starts (gap > 10 min = new block)
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
