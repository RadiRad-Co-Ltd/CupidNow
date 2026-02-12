from pathlib import Path
from app.services.parser import parse_line_chat
from app.services.cold_war import detect_cold_wars

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat_coldwar.txt"


def _parsed():
    return parse_line_chat(FIXTURE.read_text(encoding="utf-8"))


def test_detects_cold_war_period():
    result = detect_cold_wars(_parsed())
    assert len(result) >= 1


def test_cold_war_has_dates():
    result = detect_cold_wars(_parsed())
    event = result[0]
    assert "startDate" in event
    assert "endDate" in event
    assert "messageDrop" in event


def test_cold_war_dates_are_mid_march():
    result = detect_cold_wars(_parsed())
    event = result[0]
    assert "2024-03-15" <= event["startDate"] <= "2024-03-17"
