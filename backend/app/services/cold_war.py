from collections import defaultdict
from datetime import date, timedelta

from app.services.parser import Message


def detect_cold_wars(parsed: dict, drop_threshold: float = 0.5) -> list[dict]:
    """Detect periods where message volume drops significantly."""
    messages: list[Message] = parsed["messages"]
    if not messages:
        return []

    # Daily message counts (only days with messages)
    daily: dict[str, int] = defaultdict(int)
    for m in messages:
        daily[str(m.timestamp.date())] += 1

    active_dates = sorted(daily.keys())
    if len(active_dates) < 5:
        return []

    # Generate complete date range including zero-message days
    start_date = date.fromisoformat(active_dates[0])
    end_date = date.fromisoformat(active_dates[-1])
    all_dates = []
    d = start_date
    while d <= end_date:
        all_dates.append(str(d))
        d += timedelta(days=1)

    if len(all_dates) < 5:
        return []

    counts = [daily.get(d, 0) for d in all_dates]

    cold_wars = []
    in_cold_war = False
    cw_start = None
    window = min(7, len(counts))

    for i, d in enumerate(all_dates):
        count = counts[i]

        # 14-day baseline (excluding current day)
        lookback_start = max(0, i - 14)
        lookback_end = max(1, i)
        baseline_slice = counts[lookback_start:lookback_end]
        baseline = sum(baseline_slice) / len(baseline_slice) if baseline_slice else 0

        is_low = count <= max(baseline * (1 - drop_threshold), 1) if baseline > 2 else False

        if is_low and not in_cold_war:
            in_cold_war = True
            cw_start = d
        elif not is_low and in_cold_war:
            in_cold_war = False
            cold_wars.append({
                "startDate": cw_start,
                "endDate": all_dates[i - 1] if i > 0 else d,
                "messageDrop": round((1 - count / max(baseline, 1)) * 100, 1),
            })

    if in_cold_war and cw_start:
        cold_wars.append({
            "startDate": cw_start,
            "endDate": all_dates[-1],
            "messageDrop": 0,
        })

    return cold_wars
