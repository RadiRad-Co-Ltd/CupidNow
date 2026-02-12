from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


async def test_full_pipeline(client):
    """End-to-end: upload → parse → analyze → get full result."""
    resp = await client.post(
        "/api/analyze",
        data={"skip_ai": "true"},
        files={"file": ("chat.txt", FIXTURE.read_bytes(), "text/plain")},
    )

    assert resp.status_code == 200
    data = resp.json()

    assert set(data.keys()) >= {
        "persons", "basicStats", "replyBehavior",
        "timePatterns", "coldWars", "textAnalysis",
    }
    assert len(data["persons"]) == 2
    assert data["basicStats"]["messageCount"]["total"] > 0
    assert len(data["timePatterns"]["heatmap"]) == 7
    for person in data["persons"]:
        assert person in data["textAnalysis"]["wordCloud"]
