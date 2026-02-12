import base64
import os
from pathlib import Path
from app.services.encryption import encrypt_aes_gcm

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


async def test_analyze_returns_200(client):
    key = os.urandom(32)
    plaintext = FIXTURE.read_bytes()
    encrypted = encrypt_aes_gcm(plaintext, key)

    resp = await client.post(
        "/api/analyze",
        data={"key": base64.b64encode(key).decode(), "skip_ai": "true"},
        files={"file": ("chat.txt.enc", encrypted, "application/octet-stream")},
    )
    assert resp.status_code == 200


async def test_analyze_returns_basic_stats(client):
    key = os.urandom(32)
    plaintext = FIXTURE.read_bytes()
    encrypted = encrypt_aes_gcm(plaintext, key)

    resp = await client.post(
        "/api/analyze",
        data={"key": base64.b64encode(key).decode(), "skip_ai": "true"},
        files={"file": ("chat.txt.enc", encrypted, "application/octet-stream")},
    )
    data = resp.json()
    assert "basicStats" in data
    assert "replyBehavior" in data
    assert "timePatterns" in data
    assert "textAnalysis" in data
    assert "persons" in data


async def test_analyze_bad_key_returns_400(client):
    key = os.urandom(32)
    wrong_key = os.urandom(32)
    plaintext = FIXTURE.read_bytes()
    encrypted = encrypt_aes_gcm(plaintext, key)

    resp = await client.post(
        "/api/analyze",
        data={"key": base64.b64encode(wrong_key).decode(), "skip_ai": "true"},
        files={"file": ("chat.txt.enc", encrypted, "application/octet-stream")},
    )
    assert resp.status_code == 400
