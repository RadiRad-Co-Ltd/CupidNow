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
    caller: str  # who initiated the call
    duration_seconds: int  # 0 = missed call


@dataclass
class TransferRecord:
    timestamp: datetime
    sender: str   # who paid
    receiver: str  # who received
    amount: int


# Chinese format: 2024/01/15（一）
DATE_HEADER_ZH_RE = re.compile(r"^(\d{4}/\d{1,2}/\d{1,2})（[一二三四五六日]）\s*$")
# English format: 2026/01/31, Sat
DATE_HEADER_EN_RE = re.compile(r"^(\d{4}/\d{1,2}/\d{1,2}),\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s*$")

# Time: 上午09:15 / 下午02:07 / 09:15 / 10:50 PM / 6:05 AM
_TIME_PAT = r"(?:[上下]午)?\d{1,2}:\d{2}(?:\s*[APap][Mm])?"
MSG_LINE_RE = re.compile(rf"^({_TIME_PAT})\t(.+?)\t(.*)$")
CALL_LINE_2COL_RE = re.compile(rf"^({_TIME_PAT})\t☎\s*(.+)$")
CALL_LINE_3COL_RE = re.compile(rf"^({_TIME_PAT})\t(.+?)\t☎\s*(.+)$")
CALL_DURATION_RE = re.compile(r"(?:通話時間|Duration)\s*(?:(\d+):)?(\d{1,2}):(\d{2})")

TYPE_MARKERS = {
    "[貼圖]": "sticker",
    "[照片]": "photo",
    "[影片]": "video",
    "[檔案]": "file",
    "[Sticker]": "sticker",
    "[Photo]": "photo",
    "[Video]": "video",
    "[File]": "file",
}

# Transfer message patterns (LINE Pay / 轉帳)
# "已將NT$ 120轉帳給XXX。" — sender view
TRANSFER_SEND_RE = re.compile(r"已將NT\$\s*([\d,]+)\s*轉帳給(.+?)[。.]")
# "您已收到NT$ 170。（來自：XXX）" — receiver view
TRANSFER_RECV_RE = re.compile(r"您已收到NT\$\s*([\d,]+)[。.]（來自：(.+?)）")
# "收到NT$300的轉帳。" — short receiver format (no sender info)
TRANSFER_RECV_SHORT_RE = re.compile(r"收到NT\$\s*([\d,]+)\s*的轉帳[。.]")

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
# LINE emoji export format: (emoji), (salute), (toilet thumbs up), etc.
# Only match ASCII words inside parens to avoid matching Chinese text like (哈哈)
_LINE_EMOJI_RE = re.compile(r"\((?:[a-zA-Z]+(?:\s+[a-zA-Z]+){0,3})\)")


def _clean_content(content: str, msg_type: str) -> tuple[str, str]:
    """Strip URLs and LINE emoji tokens from text messages.

    Returns (cleaned_content, final_type):
    - Pure URL → 'link'
    - Pure emoji → 'emoji'
    - Mixed → remove URLs/emoji, keep text as 'text'
    """
    if msg_type != "text":
        return content, msg_type
    cleaned = _URL_RE.sub("", content)
    cleaned = _LINE_EMOJI_RE.sub("", cleaned).strip()
    if not cleaned:
        # Original had content but cleaned is empty → was all URL or emoji
        if _URL_RE.search(content):
            return content, "link"
        return content, "emoji"
    return cleaned, "text"


def _parse_time(time_str: str) -> datetime:
    """Parse time string like '09:30', '上午11:19', '下午02:07', '10:50 PM', '6:05 AM'."""
    s = time_str.strip()

    # Chinese AM/PM prefix
    is_pm = s.startswith("下午")
    is_am = s.startswith("上午")
    if is_am or is_pm:
        s = s[2:]

    # English AM/PM suffix
    s_upper = s.upper().strip()
    if s_upper.endswith("PM"):
        is_pm = True
        s = s_upper[:-2].strip()
    elif s_upper.endswith("AM"):
        is_am = True
        s = s_upper[:-2].strip()

    h, m = map(int, s.split(":"))
    if is_pm and h != 12:
        h += 12
    elif is_am and h == 12:
        h = 0
    return datetime.strptime(f"{h}:{m}", "%H:%M")


def _detect_type(content: str) -> str:
    stripped = content.strip()
    return TYPE_MARKERS.get(stripped, "text")


def _detect_transfer(content: str, sender: str, persons: set[str], timestamp: datetime) -> TransferRecord | None:
    """Try to parse a transfer message. Returns TransferRecord or None.

    Two formats carry full info:
    - "已將NT$120轉帳給XXX。" → sender paid XXX
    - "您已收到NT$170。（來自：XXX）" → XXX paid the message sender
    Short format infers the other person in a 2-person chat:
    - "收到NT$300的轉帳。" → the other person paid the message sender
    """
    # "已將NT$ 120轉帳給XXX。"
    m = TRANSFER_SEND_RE.search(content)
    if m:
        amount = int(m.group(1).replace(",", ""))
        receiver = m.group(2).strip()
        return TransferRecord(timestamp=timestamp, sender=sender, receiver=receiver, amount=amount)

    # "您已收到NT$ 170。（來自：XXX）"
    m = TRANSFER_RECV_RE.search(content)
    if m:
        amount = int(m.group(1).replace(",", ""))
        payer = m.group(2).strip()
        return TransferRecord(timestamp=timestamp, sender=payer, receiver=sender, amount=amount)

    # "收到NT$300的轉帳。" — infer payer as the other person
    m = TRANSFER_RECV_SHORT_RE.search(content)
    if m:
        amount = int(m.group(1).replace(",", ""))
        others = persons - {sender}
        payer = others.pop() if len(others) == 1 else ""
        return TransferRecord(timestamp=timestamp, sender=payer, receiver=sender, amount=amount)

    return None


def _parse_call_duration(text: str) -> int:
    if "未接來電" in text or "已取消" in text or "未接" in text or "Missed" in text or "Canceled" in text:
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
    transfers: list[TransferRecord] = []
    persons: set[str] = set()

    current_date: date | None = None

    for line in lines:
        # Try date header (Chinese or English format)
        dm = DATE_HEADER_ZH_RE.match(line) or DATE_HEADER_EN_RE.match(line)
        if dm:
            current_date = datetime.strptime(dm.group(1), "%Y/%m/%d").date()
            continue

        if current_date is None:
            continue

        # Try call line — 3-col format: time\tsender\t☎ text
        cm3 = CALL_LINE_3COL_RE.match(line)
        if cm3:
            time_str = cm3.group(1)
            caller = cm3.group(2)
            call_text = cm3.group(3)
            ts = datetime.combine(
                current_date,
                _parse_time(time_str).time(),
            )
            persons.add(caller)
            calls.append(CallRecord(
                timestamp=ts,
                caller=caller,
                duration_seconds=_parse_call_duration(call_text),
            ))
            continue

        # Try call line — 2-col format: time\t☎ text
        cm2 = CALL_LINE_2COL_RE.match(line)
        if cm2:
            time_str = cm2.group(1)
            call_text = cm2.group(2)
            ts = datetime.combine(
                current_date,
                _parse_time(time_str).time(),
            )
            calls.append(CallRecord(
                timestamp=ts,
                caller="",
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
                _parse_time(time_str).time(),
            )
            persons.add(sender)

            # Check for transfer messages before regular type detection
            transfer = _detect_transfer(content, sender, persons, ts)
            if transfer:
                transfers.append(transfer)
                messages.append(Message(
                    timestamp=ts,
                    sender=sender,
                    content=content,
                    msg_type="transfer",
                ))
                continue

            raw_type = _detect_type(content)
            clean_text, final_type = _clean_content(content, raw_type)
            messages.append(Message(
                timestamp=ts,
                sender=sender,
                content=clean_text,
                msg_type=final_type,
            ))
            continue

        # Continuation line (starts with tab, no timestamp)
        if line.startswith("\t") and messages:
            messages[-1].content += "\n" + line.lstrip("\t")
            continue

    return {
        "messages": messages,
        "calls": calls,
        "transfers": transfers,
        "persons": sorted(persons),
    }
