import re
from dataclasses import dataclass
from datetime import datetime, date


@dataclass
class Message:
    timestamp: datetime
    sender: str
    content: str
    msg_type: str  # "text", "sticker", "photo", "video", "file"


@dataclass
class CallRecord:
    timestamp: datetime
    duration_seconds: int  # 0 = missed call


DATE_HEADER_RE = re.compile(r"^(\d{4}/\d{1,2}/\d{1,2})（[一二三四五六日]）\s*$")
MSG_LINE_RE = re.compile(r"^(\d{1,2}:\d{2})\t(.+?)\t(.*)$")
CALL_LINE_RE = re.compile(r"^(\d{1,2}:\d{2})\t☎\s*(.+)$")
CALL_DURATION_RE = re.compile(r"通話時間\s*(?:(\d+):)?(\d{1,2}):(\d{2})")

TYPE_MARKERS = {
    "[貼圖]": "sticker",
    "[照片]": "photo",
    "[影片]": "video",
    "[檔案]": "file",
}


def _detect_type(content: str) -> str:
    stripped = content.strip()
    return TYPE_MARKERS.get(stripped, "text")


def _parse_call_duration(text: str) -> int:
    if "未接來電" in text or "已取消" in text:
        return 0
    m = CALL_DURATION_RE.search(text)
    if not m:
        return 0
    hours = int(m.group(1)) if m.group(1) else 0
    mins = int(m.group(2))
    secs = int(m.group(3))
    return hours * 3600 + mins * 60 + secs


def parse_line_chat(text: str) -> dict:
    lines = text.split("\n")
    messages: list[Message] = []
    calls: list[CallRecord] = []
    persons: set[str] = set()

    current_date: date | None = None

    for line in lines:
        # Try date header
        dm = DATE_HEADER_RE.match(line)
        if dm:
            current_date = datetime.strptime(dm.group(1), "%Y/%m/%d").date()
            continue

        if current_date is None:
            continue

        # Try call line
        cm = CALL_LINE_RE.match(line)
        if cm:
            time_str = cm.group(1)
            call_text = cm.group(2)
            ts = datetime.combine(
                current_date,
                datetime.strptime(time_str, "%H:%M").time(),
            )
            calls.append(CallRecord(
                timestamp=ts,
                duration_seconds=_parse_call_duration(call_text),
            ))
            continue

        # Try message line
        mm = MSG_LINE_RE.match(line)
        if mm:
            time_str = mm.group(1)
            sender = mm.group(2)
            content = mm.group(3)
            ts = datetime.combine(
                current_date,
                datetime.strptime(time_str, "%H:%M").time(),
            )
            persons.add(sender)
            messages.append(Message(
                timestamp=ts,
                sender=sender,
                content=content,
                msg_type=_detect_type(content),
            ))
            continue

        # Continuation line (starts with tab, no timestamp)
        if line.startswith("\t") and messages:
            messages[-1].content += "\n" + line.lstrip("\t")
            continue

    return {
        "messages": messages,
        "calls": calls,
        "persons": sorted(persons),
    }
