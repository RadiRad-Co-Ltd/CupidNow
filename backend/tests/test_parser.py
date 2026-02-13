from pathlib import Path
from app.services.parser import parse_line_chat, Message, CallRecord

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


def test_parse_returns_messages_and_calls():
    text = FIXTURE.read_text(encoding="utf-8")
    result = parse_line_chat(text)
    assert "messages" in result
    assert "calls" in result
    assert "persons" in result
    assert len(result["persons"]) == 2


def test_parse_message_count():
    text = FIXTURE.read_text(encoding="utf-8")
    result = parse_line_chat(text)
    # 小美: 早安～, 對呀！\n要不要出去走走, [貼圖], 今天好開心😊, 晚安～, 早～\n今天好冷喔, 下班了！, 隨便都好 = 8
    # 阿明: 早安！今天天氣好好, [照片], 我也是！晚安, 早安！, 我也是\n等等要吃什麼 = 5
    assert len(result["messages"]) == 13


def test_parse_multiline_message():
    text = FIXTURE.read_text(encoding="utf-8")
    result = parse_line_chat(text)
    # The 3rd message should be multi-line
    msg = result["messages"][2]
    assert "要不要出去走走" in msg.content
    assert "對呀！" in msg.content


def test_parse_sticker_detected():
    text = FIXTURE.read_text(encoding="utf-8")
    result = parse_line_chat(text)
    stickers = [m for m in result["messages"] if m.msg_type == "sticker"]
    assert len(stickers) == 1


def test_parse_photo_detected():
    text = FIXTURE.read_text(encoding="utf-8")
    result = parse_line_chat(text)
    photos = [m for m in result["messages"] if m.msg_type == "photo"]
    assert len(photos) == 1


def test_parse_call_records():
    text = FIXTURE.read_text(encoding="utf-8")
    result = parse_line_chat(text)
    assert len(result["calls"]) == 3
    # First call: 3-col format with duration 5:32
    assert result["calls"][0].caller == "小美"
    assert result["calls"][0].duration_seconds == 332  # 5*60 + 32
    # Second call: missed
    assert result["calls"][1].caller == "阿明"
    assert result["calls"][1].duration_seconds == 0
    # Third call: 1:23:45
    assert result["calls"][2].caller == "阿明"
    assert result["calls"][2].duration_seconds == 5025  # 1*3600 + 23*60 + 45


def test_parse_identifies_persons():
    text = FIXTURE.read_text(encoding="utf-8")
    result = parse_line_chat(text)
    assert set(result["persons"]) == {"小美", "阿明"}
