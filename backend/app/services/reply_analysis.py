from collections import defaultdict
from app.services.parser import Message

INSTANT_THRESHOLD_SECONDS = 60
TOPIC_GAP_SECONDS = 4 * 3600  # 4 hours silence = new topic


def compute_reply_behavior(parsed: dict) -> dict:
    messages: list[Message] = parsed["messages"]
    persons: list[str] = parsed["persons"]

    if len(messages) < 2:
        return _empty_result(persons)

    reply_times: dict[str, list[float]] = defaultdict(list)
    speed_buckets = {"under1min": 0, "1to5min": 0, "5to30min": 0, "30to60min": 0, "over60min": 0}
    topic_starts: dict[str, int] = defaultdict(int)

    prev = messages[0]
    for msg in messages[1:]:
        delta = (msg.timestamp - prev.timestamp).total_seconds()

        # Topic initiator: first message after long silence
        if delta >= TOPIC_GAP_SECONDS:
            topic_starts[msg.sender] += 1

        # Reply time: only when different sender
        if msg.sender != prev.sender and delta >= 0:
            reply_times[msg.sender].append(delta)

            if delta <= 60:
                speed_buckets["under1min"] += 1
            elif delta <= 300:
                speed_buckets["1to5min"] += 1
            elif delta <= 1800:
                speed_buckets["5to30min"] += 1
            elif delta <= 3600:
                speed_buckets["30to60min"] += 1
            else:
                speed_buckets["over60min"] += 1

        prev = msg

    # Instant reply rate per person
    instant_rate = {}
    avg_reply = {}
    for p in persons:
        times = reply_times[p]
        if times:
            instant_count = sum(1 for t in times if t <= INSTANT_THRESHOLD_SECONDS)
            instant_rate[p] = round(instant_count / len(times) * 100, 1)
            avg_reply[p] = round(sum(times) / len(times))
        else:
            instant_rate[p] = 0
            avg_reply[p] = 0

    return {
        "instantReplyRate": instant_rate,
        "avgReplyTime": avg_reply,
        "speedDistribution": speed_buckets,
        "topicInitiator": dict(topic_starts),
    }


def _empty_result(persons):
    return {
        "instantReplyRate": {p: 0 for p in persons},
        "avgReplyTime": {p: 0 for p in persons},
        "speedDistribution": {"under1min": 0, "1to5min": 0, "5to30min": 0, "30to60min": 0, "over60min": 0},
        "topicInitiator": {},
    }
