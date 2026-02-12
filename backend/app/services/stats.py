from app.services.parser import Message, CallRecord


def compute_basic_stats(parsed: dict) -> dict:
    messages: list[Message] = parsed["messages"]
    calls: list[CallRecord] = parsed["calls"]
    persons: list[str] = parsed["persons"]

    # Message counts
    msg_counts = {}
    word_counts = {}
    for p in persons:
        p_msgs = [m for m in messages if m.sender == p]
        msg_counts[p] = len(p_msgs)
        word_counts[p] = sum(len(m.content) for m in p_msgs if m.msg_type == "text")
    msg_counts["total"] = len(messages)
    word_counts["total"] = sum(word_counts[p] for p in persons)

    # Type breakdown
    type_counts: dict[str, int] = {}
    for m in messages:
        type_counts[m.msg_type] = type_counts.get(m.msg_type, 0) + 1

    # Call stats
    completed = [c for c in calls if c.duration_seconds > 0]
    missed = [c for c in calls if c.duration_seconds == 0]
    total_dur = sum(c.duration_seconds for c in completed)

    call_stats = {
        "totalCalls": len(calls),
        "completedCalls": len(completed),
        "missedCalls": len(missed),
        "totalDurationSeconds": total_dur,
        "avgDurationSeconds": round(total_dur / len(completed)) if completed else 0,
        "maxDurationSeconds": max((c.duration_seconds for c in completed), default=0),
    }

    # Date range
    if messages:
        dates = [m.timestamp.date() for m in messages]
        start = min(dates)
        end = max(dates)
        total_days = (end - start).days + 1
    else:
        start = end = None
        total_days = 0

    # Person balance
    total_msgs = msg_counts["total"] or 1
    total_words = word_counts["total"] or 1

    def _balance(metric: dict, total: int) -> dict:
        return {
            p: {"count": metric[p], "percent": round(metric[p] / total * 100, 1)}
            for p in persons
        }

    person_balance = {
        "messages": _balance(msg_counts, total_msgs),
        "words": _balance(word_counts, total_words),
        "stickers": _balance(
            {p: len([m for m in messages if m.sender == p and m.msg_type == "sticker"]) for p in persons},
            max(type_counts.get("sticker", 0), 1),
        ),
    }

    return {
        "messageCount": msg_counts,
        "wordCount": word_counts,
        "typeBreakdown": type_counts,
        "callStats": call_stats,
        "dateRange": {
            "start": str(start) if start else None,
            "end": str(end) if end else None,
            "totalDays": total_days,
        },
        "personBalance": person_balance,
    }
