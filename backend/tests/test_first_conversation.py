"""Tests for extract_first_conversation."""

from datetime import datetime, timedelta

import pytest

from app.services.first_conversation import extract_first_conversation
from app.services.parser import Message


def _msg(minutes_offset: int, sender: str = "小美", content: str = "嗨",
         msg_type: str = "text") -> Message:
    """Helper – create a Message at *minutes_offset* from a fixed origin."""
    origin = datetime(2024, 1, 15, 9, 0)
    return Message(
        timestamp=origin + timedelta(minutes=minutes_offset),
        sender=sender,
        content=content,
        msg_type=msg_type,
    )


def _parsed(messages: list[Message]) -> dict:
    return {"messages": messages, "persons": ["小美", "阿明"], "calls": [], "transfers": []}


# ── 1. basic return structure ────────────────────────────────────────
class TestBasicStructure:
    def test_returns_messages_startdate_isfallback(self):
        msgs = [_msg(0), _msg(5), _msg(10), _msg(15), _msg(20), _msg(25)]
        result = extract_first_conversation(_parsed(msgs))
        assert "messages" in result
        assert "startDate" in result
        assert "isFallback" in result

    def test_message_fields(self):
        msgs = [_msg(0), _msg(5), _msg(10), _msg(15), _msg(20), _msg(25)]
        result = extract_first_conversation(_parsed(msgs))
        m = result["messages"][0]
        assert set(m.keys()) == {"timestamp", "sender", "content", "msgType"}


# ── 2. empty messages → None ────────────────────────────────────────
class TestEmpty:
    def test_empty_messages_returns_none(self):
        assert extract_first_conversation(_parsed([])) is None


# ── 3. continuous burst detection ────────────────────────────────────
class TestBurstDetection:
    def test_burst_stops_at_gap(self):
        """6 dense messages + 1 next-day message → burst = 6."""
        msgs = [
            _msg(0, "小美"),
            _msg(3, "阿明"),
            _msg(7, "小美"),
            _msg(12, "阿明"),
            _msg(18, "小美"),
            _msg(25, "阿明"),
            # gap > 30 min
            _msg(25 + 60, "小美"),
        ]
        result = extract_first_conversation(_parsed(msgs))
        assert result["isFallback"] is False
        assert len(result["messages"]) == 6

    def test_start_date_matches_first_message(self):
        msgs = [_msg(0), _msg(5), _msg(10), _msg(15), _msg(20), _msg(25)]
        result = extract_first_conversation(_parsed(msgs))
        assert result["startDate"] == "2024-01-15"


# ── 4. fallback mode (burst < 5) ────────────────────────────────────
class TestFallback:
    def test_small_burst_triggers_fallback(self):
        """Only 3 messages before a big gap → fallback."""
        msgs = [
            _msg(0),
            _msg(5),
            _msg(10),
            # gap
            _msg(200),
            _msg(205),
            _msg(210),
            _msg(215),
            _msg(220),
        ]
        result = extract_first_conversation(_parsed(msgs))
        assert result["isFallback"] is True
        # fallback takes up to 20 from the beginning
        assert len(result["messages"]) == len(msgs)  # 8 < 20


# ── 5. max 50 cap ───────────────────────────────────────────────────
class TestMaxCap:
    def test_burst_capped_at_50(self):
        msgs = [_msg(i) for i in range(60)]  # 60 dense messages (1 min apart)
        result = extract_first_conversation(_parsed(msgs))
        assert len(result["messages"]) <= 50


# ── 6. non-text messages get labels ─────────────────────────────────
class TestNonTextLabels:
    def test_sticker_label(self):
        msgs = [
            _msg(0, msg_type="text"),
            _msg(5, msg_type="sticker", content="[貼圖]"),
            _msg(10, msg_type="text"),
            _msg(15, msg_type="text"),
            _msg(20, msg_type="text"),
            _msg(25, msg_type="text"),
        ]
        result = extract_first_conversation(_parsed(msgs))
        assert result["messages"][1]["content"] == "[貼圖]"
        assert result["messages"][1]["msgType"] == "sticker"

    def test_photo_label(self):
        msgs = [
            _msg(0, msg_type="text"),
            _msg(5, msg_type="photo", content="[照片]"),
            _msg(10, msg_type="text"),
            _msg(15, msg_type="text"),
            _msg(20, msg_type="text"),
            _msg(25, msg_type="text"),
        ]
        result = extract_first_conversation(_parsed(msgs))
        assert result["messages"][1]["content"] == "[照片]"
        assert result["messages"][1]["msgType"] == "photo"
