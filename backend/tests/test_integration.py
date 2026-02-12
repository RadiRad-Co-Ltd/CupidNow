import base64
import os
from pathlib import Path
from app.services.encryption import encrypt_aes_gcm

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


async def test_full_pipeline(client):
    """End-to-end: encrypt → upload → get full analysis result."""
    key = os.urandom(32)
    plaintext = FIXTURE.read_bytes()
    encrypted = encrypt_aes_gcm(plaintext, key)

    resp = await client.post(
        "/api/analyze",
        data={"key": base64.b64encode(key).decode(), "skip_ai": "true"},
        files={"file": ("chat.txt.enc", encrypted, "application/octet-stream")},
    )

    assert resp.status_code == 200
    data = resp.json()

    # Verify all sections present
    assert set(data.keys()) >= {
        "persons", "basicStats", "replyBehavior",
        "timePatterns", "coldWars", "textAnalysis",
    }

    # Verify persons detected
    assert len(data["persons"]) == 2

    # Verify basic stats have numbers
    assert data["basicStats"]["messageCount"]["total"] > 0

    # Verify heatmap shape
    assert len(data["timePatterns"]["heatmap"]) == 7

    # Verify text analysis has word clouds
    for person in data["persons"]:
        assert person in data["textAnalysis"]["wordCloud"]
