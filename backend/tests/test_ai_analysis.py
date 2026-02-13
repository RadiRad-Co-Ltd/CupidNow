from app.services.ai_analysis import sample_messages, build_prompt, _is_meaningful, _sentiment_intensity
from app.services.parser import Message
from datetime import datetime


def _make_messages():
    base = datetime(2024, 1, 15, 9, 0)
    msgs = []
    for i in range(50):
        msgs.append(Message(
            timestamp=base.replace(hour=9 + (i % 12)),
            sender="小美" if i % 2 == 0 else "阿明",
            content=f"今天去看了一部超好看的電影 {i}",
            msg_type="text",
        ))
    return msgs


def test_sample_messages_caps_at_max():
    msgs = _make_messages()
    sampled = sample_messages(msgs, max_total=10)
    assert len(sampled) == 10


def test_sample_messages_empty_input():
    assert sample_messages([]) == []


def test_filters_trivial_messages():
    base = datetime(2024, 1, 15, 10, 0)
    msgs = [
        Message(timestamp=base, sender="A", content="嗯嗯", msg_type="text"),
        Message(timestamp=base, sender="A", content="好喔", msg_type="text"),
        Message(timestamp=base, sender="A", content="哈哈哈哈", msg_type="text"),
        Message(timestamp=base, sender="A", content="OK", msg_type="text"),
        Message(timestamp=base, sender="A", content="今天工作好累想找你聊天", msg_type="text"),
    ]
    sampled = sample_messages(msgs)
    assert len(sampled) == 1
    assert sampled[0].content == "今天工作好累想找你聊天"


def test_is_meaningful():
    assert not _is_meaningful("嗯")
    assert not _is_meaningful("好啊")
    assert not _is_meaningful("哈哈哈哈哈哈")
    assert not _is_meaningful("!!!")
    assert not _is_meaningful("XD")
    assert _is_meaningful("今天天氣真好")
    assert _is_meaningful("我好想你喔")


def test_build_prompt_contains_messages():
    msgs = _make_messages()[:5]
    prompt = build_prompt(msgs, ["小美", "阿明"])
    assert "小美" in prompt
    assert "阿明" in prompt
    assert "電影" in prompt


def test_build_prompt_asks_for_json():
    msgs = _make_messages()[:5]
    prompt = build_prompt(msgs, ["小美", "阿明"])
    assert "JSON" in prompt


def test_sentiment_intensity():
    # Emotional messages should have higher intensity than neutral ones
    intense = _sentiment_intensity("我真的好愛你")
    neutral = _sentiment_intensity("今天星期三")
    assert intense > neutral


def test_sample_prioritizes_emotional_messages():
    base = datetime(2024, 1, 15, 10, 0)
    msgs = [
        Message(timestamp=base.replace(minute=0), sender="A",
                content="今天吃了午餐便當", msg_type="text"),
        Message(timestamp=base.replace(minute=1), sender="A",
                content="我真的好討厭這件事情", msg_type="text"),
        Message(timestamp=base.replace(minute=2), sender="A",
                content="超級開心今天收到禮物", msg_type="text"),
        Message(timestamp=base.replace(minute=3), sender="A",
                content="剛剛走過公園回到家", msg_type="text"),
    ]
    # Only keep 2 — should prefer the emotional ones
    sampled = sample_messages(msgs, max_total=2)
    assert len(sampled) == 2
    contents = {m.content for m in sampled}
    # At least one of the emotional messages should be kept
    emotional = {"我真的好討厭這件事情", "超級開心今天收到禮物"}
    assert len(contents & emotional) >= 1
