from pathlib import Path
from app.services.parser import parse_line_chat
from app.services.time_patterns import compute_time_patterns

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


def _parsed():
    return parse_line_chat(FIXTURE.read_text(encoding="utf-8"))


def test_heatmap_shape():
    result = compute_time_patterns(_parsed())
    heatmap = result["heatmap"]
    # 7 days x 8 time slots (3-hour blocks)
    assert len(heatmap) == 7
    assert all(len(row) == 8 for row in heatmap)


def test_heatmap_has_values():
    result = compute_time_patterns(_parsed())
    total = sum(sum(row) for row in result["heatmap"])
    assert total > 0


def test_monthly_trend():
    result = compute_time_patterns(_parsed())
    trend = result["trend"]
    assert len(trend) > 0
    first = trend[0]
    assert "period" in first
    for person in _parsed()["persons"]:
        assert person in first


def test_goodnight_analysis():
    result = compute_time_patterns(_parsed())
    gn = result["goodnightAnalysis"]
    assert "whoSaysGoodnightFirst" in gn
    assert "whoSaysGoodmorningFirst" in gn
    assert "avgLastChatTime" in gn
