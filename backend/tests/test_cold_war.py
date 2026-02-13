from pathlib import Path
from app.services.parser import parse_line_chat
from app.services.cold_war import detect_cold_wars

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat_coldwar.txt"


def _parsed():
    return parse_line_chat(FIXTURE.read_text(encoding="utf-8"))


def test_short_dip_not_detected_with_default():
    """A 3-day dip should NOT be detected with default min_days=7."""
    result = detect_cold_wars(_parsed())
    assert result == []


def test_detects_cold_war_with_lower_min_days():
    """A 3-day dip IS detected when min_days is lowered."""
    result = detect_cold_wars(_parsed(), min_days=2)
    assert len(result) >= 1


def test_cold_war_has_dates():
    result = detect_cold_wars(_parsed(), min_days=2)
    event = result[0]
    assert "startDate" in event
    assert "endDate" in event
    assert "messageDrop" in event


def test_cold_war_dates_are_mid_march():
    result = detect_cold_wars(_parsed(), min_days=2)
    event = result[0]
    assert "2024-03-15" <= event["startDate"] <= "2024-03-17"


def test_cold_war_fewer_than_5_days_returns_empty():
    """Chats shorter than 7 days should return no cold wars."""
    short = Path(__file__).parent / "fixtures" / "sample_chat.txt"
    parsed = parse_line_chat(short.read_text(encoding="utf-8"))
    result = detect_cold_wars(parsed)
    assert result == []


def test_cold_war_empty_messages():
    result = detect_cold_wars({"messages": [], "persons": [], "calls": []})
    assert result == []
