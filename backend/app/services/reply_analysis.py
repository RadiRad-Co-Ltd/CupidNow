from collections import defaultdict
from app.services.parser import Message

INSTANT_THRESHOLD_SECONDS = 60
REPLY_CAP_SECONDS = 3600  # ignore gaps > 1 hour for avg reply time
SLEEP_START_HOUR = 2   # 凌晨 2 點
SLEEP_END_HOUR = 8     # 早上 8 點


def _is_sleep_gap(prev: Message, curr: Message) -> bool:
    """Return True if the gap between messages is likely overnight sleep."""
    prev_h = prev.timestamp.hour
    curr_h = curr.timestamp.hour
    prev_before_sleep = prev_h >= 20 or prev_h < SLEEP_START_HOUR
    curr_after_wake = SLEEP_END_HOUR <= curr_h < 12
    delta_hours = (curr.timestamp - prev.timestamp).total_seconds() / 3600
    return prev_before_sleep and curr_after_wake and 4 <= delta_hours <= 14


def compute_reply_behavior(parsed: dict) -> dict:
    messages: list[Message] = parsed["messages"]
    persons: list[str] = parsed["persons"]

    if len(messages) < 2:
        return _empty_result(persons)

    reply_times: dict[str, list[float]] = defaultdict(list)
    speed_buckets = {"<1m": 0, "1-5m": 0, "5-30m": 0, "30m-1h": 0, ">1h": 0}

    # Streak tracking: longest consecutive conversation (gap < 5 min between messages)
    streak_threshold = 300  # 5 minutes
    current_streak = 1
    longest_streak = 1
    longest_streak_date = messages[0].timestamp.date()

    # Read-left-on-read: last message in a conversation with no reply for > 1 hour
    left_on_read: dict[str, int] = defaultdict(int)

    prev = messages[0]
    for msg in messages[1:]:
        delta = (msg.timestamp - prev.timestamp).total_seconds()

        # Streak tracking
        if delta <= streak_threshold:
            current_streak += 1
        else:
            if current_streak > longest_streak:
                longest_streak = current_streak
                longest_streak_date = prev.timestamp.date()
            current_streak = 1

        # Left on read: if gap > 1 hour AND same sender didn't double-text AND not sleep
        if delta > REPLY_CAP_SECONDS and msg.sender != prev.sender and not _is_sleep_gap(prev, msg):
            left_on_read[prev.sender] += 1

        # Reply time: only when different sender
        if msg.sender != prev.sender and delta >= 0:
            reply_times[msg.sender].append(delta)

            if delta <= 60:
                speed_buckets["<1m"] += 1
            elif delta <= 300:
                speed_buckets["1-5m"] += 1
            elif delta <= 1800:
                speed_buckets["5-30m"] += 1
            elif delta <= 3600:
                speed_buckets["30m-1h"] += 1
            else:
                speed_buckets[">1h"] += 1

        prev = msg

    # Check final streak
    if current_streak > longest_streak:
        longest_streak = current_streak
        longest_streak_date = prev.timestamp.date()

    # Instant reply rate per person (as 0-100 percentage)
    instant_rate = {}
    avg_reply = {}
    for p in persons:
        times = reply_times[p]
        if times:
            instant_count = sum(1 for t in times if t <= INSTANT_THRESHOLD_SECONDS)
            instant_rate[p] = round(instant_count / len(times) * 100, 1)
            # Average reply: only count replies within 1 hour (exclude offline/sleep)
            active_times = [t for t in times if t <= REPLY_CAP_SECONDS]
            avg_reply[p] = round(sum(active_times) / len(active_times)) if active_times else 0
        else:
            instant_rate[p] = 0
            avg_reply[p] = 0

    return {
        "instantReplyRate": instant_rate,
        "avgReplyTime": avg_reply,
        "speedDistribution": speed_buckets,
        "longestStreak": {
            "count": longest_streak,
            "date": str(longest_streak_date),
        },
        "leftOnRead": dict(left_on_read),
    }


def _empty_result(persons):
    return {
        "instantReplyRate": {p: 0 for p in persons},
        "avgReplyTime": {p: 0 for p in persons},
        "speedDistribution": {"<1m": 0, "1-5m": 0, "5-30m": 0, "30m-1h": 0, ">1h": 0},
        "longestStreak": {"count": 0, "date": ""},
        "leftOnRead": {},
    }
