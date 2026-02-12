from app.services.ai_analysis import sample_messages, build_prompt
from app.services.parser import Message
from datetime import datetime


def _make_messages():
    base = datetime(2024, 1, 15, 9, 0)
    msgs = []
    for i in range(50):
        msgs.append(Message(
            timestamp=base.replace(hour=9 + (i % 12)),
            sender="小美" if i % 2 == 0 else "阿明",
            content=f"測試訊息 {i}",
            msg_type="text",
        ))
    return msgs


def test_sample_messages_reduces_count():
    msgs = _make_messages()
    sampled = sample_messages(msgs, per_day=5)
    assert len(sampled) <= 10  # 1 day * up to 5*2


def test_sample_messages_empty_input():
    sampled = sample_messages([], per_day=5)
    assert sampled == []


def test_build_prompt_contains_messages():
    msgs = _make_messages()[:5]
    prompt = build_prompt(msgs, ["小美", "阿明"])
    assert "小美" in prompt
    assert "阿明" in prompt
    assert "測試訊息" in prompt


def test_build_prompt_asks_for_json():
    msgs = _make_messages()[:5]
    prompt = build_prompt(msgs, ["小美", "阿明"])
    assert "JSON" in prompt
