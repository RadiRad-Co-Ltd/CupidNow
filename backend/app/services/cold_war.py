from collections import defaultdict
from app.services.parser import Message


def detect_cold_wars(parsed: dict, drop_threshold: float = 0.5) -> list[dict]:
    """Detect periods where message volume drops significantly."""
    messages: list[Message] = parsed["messages"]
    if not messages:
        return []

    # Daily message counts
    daily: dict[str, int] = defaultdict(int)
    for m in messages:
        daily[str(m.timestamp.date())] += 1

    dates = sorted(daily.keys())
    if len(dates) < 5:
        return []

    # Compute 7-day rolling average
    counts = [daily.get(d, 0) for d in dates]
    window = min(7, len(counts))
    rolling_avg = sum(counts[:window]) / window

    cold_wars = []
    in_cold_war = False
    cw_start = None

    for i, d in enumerate(dates):
        count = counts[i]

        # Update rolling avg (simple moving)
        start_idx = max(0, i - window)
        rolling_avg = sum(counts[start_idx:i + 1]) / (i - start_idx + 1)

        # Check for significant drop
        baseline = sum(counts[max(0, i - 14):max(1, i)]) / max(1, min(14, i))
        is_low = count <= max(baseline * (1 - drop_threshold), 1) if baseline > 2 else False

        if is_low and not in_cold_war:
            in_cold_war = True
            cw_start = d
        elif not is_low and in_cold_war:
            in_cold_war = False
            cold_wars.append({
                "startDate": cw_start,
                "endDate": dates[i - 1] if i > 0 else d,
                "messageDrop": round((1 - count / max(baseline, 1)) * 100, 1),
            })

    if in_cold_war and cw_start:
        cold_wars.append({
            "startDate": cw_start,
            "endDate": dates[-1],
            "messageDrop": 0,
        })

    return cold_wars
