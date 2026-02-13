from collections import defaultdict
from datetime import date, timedelta

from app.services.parser import Message


def detect_cold_wars(
    parsed: dict,
    drop_threshold: float = 0.65,
    min_days: int = 7,
    baseline_window: int = 30,
) -> list[dict]:
    """Detect periods where message volume drops significantly.

    Args:
        drop_threshold: Minimum drop ratio to count as cold war (0.65 = 65% drop)
        min_days: Minimum consecutive low days to qualify
        baseline_window: Days of history used to compute normal volume
    """
    messages: list[Message] = parsed["messages"]
    if not messages:
        return []

    # Daily message counts
    daily: dict[str, int] = defaultdict(int)
    for m in messages:
        daily[str(m.timestamp.date())] += 1

    active_dates = sorted(daily.keys())
    if len(active_dates) < 7:
        return []

    # Complete date range including zero-message days
    start_date = date.fromisoformat(active_dates[0])
    end_date = date.fromisoformat(active_dates[-1])
    all_dates: list[str] = []
    d = start_date
    while d <= end_date:
        all_dates.append(str(d))
        d += timedelta(days=1)

    if len(all_dates) < 7:
        return []

    counts = [daily.get(d, 0) for d in all_dates]

    # Mark each day as "low" if it falls significantly below the rolling baseline
    low_flags: list[bool] = []
    for i in range(len(all_dates)):
        lookback_start = max(0, i - baseline_window)
        baseline_slice = counts[lookback_start:i]  # exclude current day
        if len(baseline_slice) < 3:
            low_flags.append(False)
            continue
        baseline = sum(baseline_slice) / len(baseline_slice)
        if baseline < 3:
            # Not enough baseline volume to judge
            low_flags.append(False)
            continue
        threshold = baseline * (1 - drop_threshold)
        low_flags.append(counts[i] <= max(threshold, 1))

    # Extract consecutive low-day runs of at least min_days
    cold_wars: list[dict] = []
    run_start = None
    for i, is_low in enumerate(low_flags):
        if is_low and run_start is None:
            run_start = i
        elif not is_low and run_start is not None:
            run_end = i - 1
            if run_end - run_start + 1 >= min_days:
                cold_wars.append(_build_event(
                    all_dates, counts, run_start, run_end, baseline_window,
                ))
            run_start = None

    # Handle run that extends to the end
    if run_start is not None:
        run_end = len(all_dates) - 1
        if run_end - run_start + 1 >= min_days:
            cold_wars.append(_build_event(
                all_dates, counts, run_start, run_end, baseline_window,
            ))

    return cold_wars


def _build_event(
    all_dates: list[str],
    counts: list[int],
    start_idx: int,
    end_idx: int,
    baseline_window: int,
) -> dict:
    """Build a cold war event with accurate messageDrop percentage."""
    cw_counts = counts[start_idx : end_idx + 1]
    cw_avg = sum(cw_counts) / len(cw_counts)

    # Baseline: average of the baseline_window days before the cold war
    bl_start = max(0, start_idx - baseline_window)
    bl_slice = counts[bl_start:start_idx]
    baseline = sum(bl_slice) / len(bl_slice) if bl_slice else 1

    drop_pct = round((1 - cw_avg / max(baseline, 1)) * 100)
    return {
        "startDate": all_dates[start_idx],
        "endDate": all_dates[end_idx],
        "messageDrop": max(drop_pct, 0),
    }
