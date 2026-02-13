from pathlib import Path
from app.services.parser import parse_line_chat
from app.services.stats import compute_basic_stats

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


def _parsed():
    return parse_line_chat(FIXTURE.read_text(encoding="utf-8"))


def test_message_count_per_person():
    result = compute_basic_stats(_parsed())
    counts = result["messageCount"]
    assert counts["小美"] > 0
    assert counts["阿明"] > 0
    assert counts["小美"] + counts["阿明"] == counts["total"]


def test_word_count():
    result = compute_basic_stats(_parsed())
    wc = result["wordCount"]
    assert wc["total"] > 0
    assert "小美" in wc
    assert "阿明" in wc


def test_type_breakdown():
    result = compute_basic_stats(_parsed())
    types = result["typeBreakdown"]
    assert types["sticker"] == 1
    assert types["photo"] == 1
    assert types["text"] >= 1


def test_call_stats():
    result = compute_basic_stats(_parsed())
    cs = result["callStats"]
    assert cs["totalCalls"] == 3
    assert cs["completedCalls"] == 2
    assert cs["missedCalls"] == 1
    assert cs["totalDurationSeconds"] == 332 + 5025


def test_date_range():
    result = compute_basic_stats(_parsed())
    assert result["dateRange"]["start"] == "2024-01-15"
    assert result["dateRange"]["end"] == "2024-01-16"
    assert result["dateRange"]["totalDays"] == 2


def test_person_balance():
    result = compute_basic_stats(_parsed())
    bal = result["personBalance"]
    # Structure: bal[person][metric] = {count, percent}
    assert "小美" in bal
    assert "阿明" in bal
    assert bal["小美"]["text"]["percent"] > 0
    assert bal["小美"]["call"]["count"] == 1
    assert bal["阿明"]["call"]["count"] == 2


def test_empty_messages():
    parsed = {"messages": [], "persons": [], "calls": []}
    result = compute_basic_stats(parsed)
    assert result["messageCount"]["total"] == 0
    assert result["dateRange"]["totalDays"] == 0
