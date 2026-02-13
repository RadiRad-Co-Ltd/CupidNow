from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


async def test_analyze_returns_200(client):
    resp = await client.post(
        "/api/analyze",
        data={"skip_ai": "true"},
        files={"file": ("chat.txt", FIXTURE.read_bytes(), "text/plain")},
    )
    assert resp.status_code == 200


async def test_analyze_returns_all_sections(client):
    resp = await client.post(
        "/api/analyze",
        data={"skip_ai": "true"},
        files={"file": ("chat.txt", FIXTURE.read_bytes(), "text/plain")},
    )
    data = resp.json()
    assert "basicStats" in data
    assert "replyBehavior" in data
    assert "timePatterns" in data
    assert "textAnalysis" in data
    assert "persons" in data


async def test_analyze_invalid_file_returns_400(client):
    resp = await client.post(
        "/api/analyze",
        data={"skip_ai": "true"},
        files={"file": ("chat.txt", b"just some random text", "text/plain")},
    )
    assert resp.status_code == 400


async def test_analyze_oversized_file_returns_413(client):
    big = b"x" * (21 * 1024 * 1024)
    resp = await client.post(
        "/api/analyze",
        data={"skip_ai": "true"},
        files={"file": ("chat.txt", big, "text/plain")},
    )
    assert resp.status_code == 413
