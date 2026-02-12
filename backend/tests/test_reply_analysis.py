from pathlib import Path
from app.services.parser import parse_line_chat
from app.services.reply_analysis import compute_reply_behavior

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


def _parsed():
    return parse_line_chat(FIXTURE.read_text(encoding="utf-8"))


def test_instant_reply_rate():
    result = compute_reply_behavior(_parsed())
    rates = result["instantReplyRate"]
    # Both persons should have a rate between 0-100
    for person in _parsed()["persons"]:
        assert 0 <= rates[person] <= 100


def test_avg_reply_time():
    result = compute_reply_behavior(_parsed())
    avg = result["avgReplyTime"]
    for person in _parsed()["persons"]:
        assert person in avg
        assert avg[person] >= 0


def test_speed_distribution():
    result = compute_reply_behavior(_parsed())
    dist = result["speedDistribution"]
    # Should have categories
    assert "under1min" in dist
    assert "1to5min" in dist
    assert "5to30min" in dist
    assert "30to60min" in dist
    assert "over60min" in dist


def test_topic_initiator():
    result = compute_reply_behavior(_parsed())
    init = result["topicInitiator"]
    total = sum(init[p] for p in init)
    assert total >= 1


def test_single_message_returns_empty_result():
    """A single message should return zeroed-out results."""
    from app.services.parser import Message
    from datetime import datetime

    parsed = {
        "messages": [Message(timestamp=datetime(2024, 1, 1, 9, 0), sender="A", content="hi", msg_type="text")],
        "persons": ["A", "B"],
        "calls": [],
    }
    result = compute_reply_behavior(parsed)
    assert result["instantReplyRate"]["A"] == 0
    assert result["instantReplyRate"]["B"] == 0
    assert result["avgReplyTime"]["A"] == 0


def test_empty_messages_returns_empty_result():
    parsed = {"messages": [], "persons": ["A", "B"], "calls": []}
    result = compute_reply_behavior(parsed)
    assert result["instantReplyRate"]["A"] == 0
