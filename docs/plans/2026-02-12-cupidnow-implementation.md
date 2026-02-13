# CupidNow Implementation Plan

> **狀態**：所有 17 個 Task 已完成。已部署上線。
> - 前端：https://cupidnow.netlify.app (Netlify)
> - 後端：https://cupidnow-api.onrender.com (Render Docker)

**Goal:** Build a web application that analyzes LINE chat txt exports to visualize chat frequency, engagement patterns, and emotional dynamics between two people — suitable for both 曖昧 and 戀愛 stages.

**Architecture:** Frontend-backend separation. React + Vite frontend handles data visualization. Python + FastAPI backend handles LINE txt parsing, statistical analysis, text analysis, and Claude API calls. All processing is memory-only with immediate cleanup.

**Tech Stack (Actual):** React 19, Vite 7, Tailwind CSS v4, Lucide React, html-to-image, TypeScript 5.9 | Python 3.12, FastAPI, pandas, jieba, anthropic SDK

**Changes from Original Plan:**
- ~~Recharts~~ → 自製 CSS 圖表元件
- ~~AES-256-GCM 加密~~ → HTTPS 明文傳輸 + 伺服器端安全措施（速率限制、CORS、檔案大小限制）
- ~~html2canvas~~ → html-to-image（支援 Tailwind v4 的 oklch/oklab 色彩函數）
- ~~SSE 進度推送~~ → 簡易前端進度條
- 新增 Lucide React 圖示庫（取代 emoji）
- 新增 Web Share API 社群分享功能
- 新增手機 RWD 直式排版

**Design Reference:** UI mockup at `designs/cupidnow-ui.pen` — design tokens listed below.

**Design Tokens (from UI mockup):**
```
--rose-primary: #E8457E    --purple-accent: #9F7AEA
--rose-dark: #C4225D       --gold-accent: #F5A623
--teal-positive: #38B2AC   --coral-warm: #FF7E7E
--bg-page: #FFF8FA         --bg-card: #FFFFFF
--bg-blush: #FFF0F3        --bg-hero-dark: #2D1B33
--text-primary: #2D1F3D    --text-secondary: #7A6B8A
--text-muted: #B8ADC7      --border-light: #F3E8EE
--gradient-start: #E8457E  --gradient-end: #9F7AEA
Fonts: "Plus Jakarta Sans" (headings), "Inter" (body)
Corner radius: 20px (cards), 12px (buttons/inputs)
```

---

## Phase 1 — Core MVP

### Task 1: Backend Project Scaffold

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/.python-version`

**Step 1: Create pyproject.toml**

```toml
# backend/pyproject.toml
[project]
name = "cupidnow-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "python-multipart>=0.0.18",
    "pycryptodome>=3.21",
    "pandas>=2.2",
    "jieba>=0.42",
    "anthropic>=0.43",
    "sse-starlette>=2.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.25",
    "httpx>=0.28",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 2: Create FastAPI entry point**

```python
# backend/app/__init__.py
# (empty)
```

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CupidNow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

**Step 3: Create test conftest**

```python
# backend/tests/__init__.py
# (empty)
```

```python
# backend/tests/conftest.py
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

**Step 4: Install and run health check test**

```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Create a quick smoke test:

```python
# backend/tests/test_health.py
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

Run: `cd backend && python -m pytest tests/test_health.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/
git commit -m "feat: scaffold backend with FastAPI and health endpoint"
```

---

### Task 2: LINE txt Parser — Core Parsing

The LINE txt parser is the foundation of everything. It must handle the various export formats LINE uses.

**LINE export format (typical):**
```
[LINE] 與○○的聊天記錄
儲存日期：2025/02/10 14:00

2024/01/15（一）
09:15	小美	早安～
09:16	阿明	早安！今天天氣好好
09:17	小美	對呀！
	要不要出去走走
12:30	小美	[貼圖]
12:31	阿明	[照片]
14:00	☎ 通話時間 5:32
22:46	阿明	晚安
```

Key edge cases:
- Multi-line messages (continuation lines start with a tab but no timestamp)
- Stickers: `[貼圖]`
- Photos: `[照片]`
- Videos: `[影片]`
- Files: `[檔案]`
- Call records: `☎ 通話時間 H:MM:SS` or `☎ 未接來電`
- System messages (no sender tab pattern)
- Date header lines: `2024/01/15（一）`

**Files:**
- Create: `backend/app/services/parser.py`
- Create: `backend/tests/test_parser.py`
- Create: `backend/tests/fixtures/sample_chat.txt`

**Step 1: Create the sample fixture file**

```text
# backend/tests/fixtures/sample_chat.txt
[LINE] 與小美的聊天記錄
儲存日期：2025/02/10 14:00

2024/01/15（一）
09:15	小美	早安～
09:16	阿明	早安！今天天氣好好
09:17	小美	對呀！
	要不要出去走走
12:30	小美	[貼圖]
12:31	阿明	[照片]
14:00	☎ 通話時間 5:32
22:45	小美	今天好開心😊
22:46	阿明	我也是！晚安
22:47	小美	晚安～
2024/01/16（二）
08:30	阿明	早安！
08:35	小美	早～
	今天好冷喔
10:00	☎ 未接來電
18:00	小美	下班了！
18:02	阿明	我也是
	等等要吃什麼
18:03	小美	隨便都好
```

**Step 2: Write failing tests**

```python
# backend/tests/test_parser.py
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
    assert len(result["calls"]) == 2
    # First call has duration
    assert result["calls"][0].duration_seconds == 332  # 5*60 + 32
    # Second call is missed
    assert result["calls"][1].duration_seconds == 0


def test_parse_identifies_persons():
    text = FIXTURE.read_text(encoding="utf-8")
    result = parse_line_chat(text)
    assert set(result["persons"]) == {"小美", "阿明"}
```

Run: `cd backend && python -m pytest tests/test_parser.py -v`
Expected: FAIL (module not found)

**Step 3: Implement parser**

```python
# backend/app/services/parser.py
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
```

**Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_parser.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/services/parser.py backend/tests/test_parser.py backend/tests/fixtures/
git commit -m "feat: implement LINE txt chat parser with multi-line and call support"
```

---

### Task 3: Basic Stats Engine

**Files:**
- Create: `backend/app/services/stats.py`
- Create: `backend/tests/test_stats.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_stats.py
from pathlib import Path
from app.services.parser import parse_line_chat
from app.services.stats import compute_basic_stats

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


def _parsed():
    return parse_line_chat(FIXTURE.read_text(encoding="utf-8"))


def test_message_count_per_person():
    result = compute_basic_stats(_parsed())
    counts = result["messageCount"]
    assert counts["小美"] > 0
    assert counts["阿明"] > 0
    assert counts["小美"] + counts["阿明"] == counts["total"]


def test_word_count():
    result = compute_basic_stats(_parsed())
    wc = result["wordCount"]
    assert wc["total"] > 0
    assert "小美" in wc
    assert "阿明" in wc


def test_type_breakdown():
    result = compute_basic_stats(_parsed())
    types = result["typeBreakdown"]
    assert types["sticker"] == 1
    assert types["photo"] == 1
    assert types["text"] >= 1


def test_call_stats():
    result = compute_basic_stats(_parsed())
    cs = result["callStats"]
    assert cs["totalCalls"] == 2
    assert cs["completedCalls"] == 1
    assert cs["missedCalls"] == 1
    assert cs["totalDurationSeconds"] == 332


def test_date_range():
    result = compute_basic_stats(_parsed())
    assert result["dateRange"]["start"] == "2024-01-15"
    assert result["dateRange"]["end"] == "2024-01-16"
    assert result["dateRange"]["totalDays"] == 2


def test_person_balance():
    result = compute_basic_stats(_parsed())
    bal = result["personBalance"]
    assert "messages" in bal
    assert "words" in bal
    # Each has person1, person2 with percentage
    assert bal["messages"]["小美"]["percent"] > 0
```

Run: `cd backend && python -m pytest tests/test_stats.py -v`
Expected: FAIL

**Step 2: Implement stats engine**

```python
# backend/app/services/stats.py
from app.services.parser import Message, CallRecord


def compute_basic_stats(parsed: dict) -> dict:
    messages: list[Message] = parsed["messages"]
    calls: list[CallRecord] = parsed["calls"]
    persons: list[str] = parsed["persons"]

    # Message counts
    msg_counts = {}
    word_counts = {}
    for p in persons:
        p_msgs = [m for m in messages if m.sender == p]
        msg_counts[p] = len(p_msgs)
        word_counts[p] = sum(len(m.content) for m in p_msgs if m.msg_type == "text")
    msg_counts["total"] = len(messages)
    word_counts["total"] = sum(word_counts[p] for p in persons)

    # Type breakdown
    type_counts: dict[str, int] = {}
    for m in messages:
        type_counts[m.msg_type] = type_counts.get(m.msg_type, 0) + 1

    # Call stats
    completed = [c for c in calls if c.duration_seconds > 0]
    missed = [c for c in calls if c.duration_seconds == 0]
    total_dur = sum(c.duration_seconds for c in completed)

    call_stats = {
        "totalCalls": len(calls),
        "completedCalls": len(completed),
        "missedCalls": len(missed),
        "totalDurationSeconds": total_dur,
        "avgDurationSeconds": round(total_dur / len(completed)) if completed else 0,
        "maxDurationSeconds": max((c.duration_seconds for c in completed), default=0),
    }

    # Date range
    if messages:
        dates = [m.timestamp.date() for m in messages]
        start = min(dates)
        end = max(dates)
        total_days = (end - start).days + 1
    else:
        start = end = None
        total_days = 0

    # Person balance
    total_msgs = msg_counts["total"] or 1
    total_words = word_counts["total"] or 1

    def _balance(metric: dict, total: int) -> dict:
        return {
            p: {"count": metric[p], "percent": round(metric[p] / total * 100, 1)}
            for p in persons
        }

    person_balance = {
        "messages": _balance(msg_counts, total_msgs),
        "words": _balance(word_counts, total_words),
        "stickers": _balance(
            {p: len([m for m in messages if m.sender == p and m.msg_type == "sticker"]) for p in persons},
            max(type_counts.get("sticker", 0), 1),
        ),
    }

    return {
        "messageCount": msg_counts,
        "wordCount": word_counts,
        "typeBreakdown": type_counts,
        "callStats": call_stats,
        "dateRange": {
            "start": str(start) if start else None,
            "end": str(end) if end else None,
            "totalDays": total_days,
        },
        "personBalance": person_balance,
    }
```

**Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_stats.py -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add backend/app/services/stats.py backend/tests/test_stats.py
git commit -m "feat: implement basic stats engine with person balance"
```

---

### Task 4: Reply Behavior Analysis

**Files:**
- Create: `backend/app/services/reply_analysis.py`
- Create: `backend/tests/test_reply_analysis.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_reply_analysis.py
from pathlib import Path
from app.services.parser import parse_line_chat
from app.services.reply_analysis import compute_reply_behavior

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


def _parsed():
    return parse_line_chat(FIXTURE.read_text(encoding="utf-8"))


def test_instant_reply_rate():
    result = compute_reply_behavior(_parsed())
    rates = result["instantReplyRate"]
    # Both persons should have a rate between 0-100
    for person in _parsed()["persons"]:
        assert 0 <= rates[person] <= 100


def test_avg_reply_time():
    result = compute_reply_behavior(_parsed())
    avg = result["avgReplyTime"]
    for person in _parsed()["persons"]:
        assert person in avg
        assert avg[person] >= 0


def test_speed_distribution():
    result = compute_reply_behavior(_parsed())
    dist = result["speedDistribution"]
    # Should have categories
    assert "under1min" in dist
    assert "1to5min" in dist
    assert "5to30min" in dist
    assert "30to60min" in dist
    assert "over60min" in dist


def test_topic_initiator():
    result = compute_reply_behavior(_parsed())
    init = result["topicInitiator"]
    total = sum(init[p] for p in init)
    assert total >= 1
```

Run: `cd backend && python -m pytest tests/test_reply_analysis.py -v`
Expected: FAIL

**Step 2: Implement reply behavior**

```python
# backend/app/services/reply_analysis.py
from collections import defaultdict
from app.services.parser import Message

INSTANT_THRESHOLD_SECONDS = 60
TOPIC_GAP_SECONDS = 4 * 3600  # 4 hours silence = new topic


def compute_reply_behavior(parsed: dict) -> dict:
    messages: list[Message] = parsed["messages"]
    persons: list[str] = parsed["persons"]

    if len(messages) < 2:
        return _empty_result(persons)

    reply_times: dict[str, list[float]] = defaultdict(list)
    speed_buckets = {"under1min": 0, "1to5min": 0, "5to30min": 0, "30to60min": 0, "over60min": 0}
    topic_starts: dict[str, int] = defaultdict(int)

    prev = messages[0]
    for msg in messages[1:]:
        delta = (msg.timestamp - prev.timestamp).total_seconds()

        # Topic initiator: first message after long silence
        if delta >= TOPIC_GAP_SECONDS:
            topic_starts[msg.sender] += 1

        # Reply time: only when different sender
        if msg.sender != prev.sender and delta >= 0:
            reply_times[msg.sender].append(delta)

            if delta <= 60:
                speed_buckets["under1min"] += 1
            elif delta <= 300:
                speed_buckets["1to5min"] += 1
            elif delta <= 1800:
                speed_buckets["5to30min"] += 1
            elif delta <= 3600:
                speed_buckets["30to60min"] += 1
            else:
                speed_buckets["over60min"] += 1

        prev = msg

    # Instant reply rate per person
    instant_rate = {}
    avg_reply = {}
    for p in persons:
        times = reply_times[p]
        if times:
            instant_count = sum(1 for t in times if t <= INSTANT_THRESHOLD_SECONDS)
            instant_rate[p] = round(instant_count / len(times) * 100, 1)
            avg_reply[p] = round(sum(times) / len(times))
        else:
            instant_rate[p] = 0
            avg_reply[p] = 0

    return {
        "instantReplyRate": instant_rate,
        "avgReplyTime": avg_reply,
        "speedDistribution": speed_buckets,
        "topicInitiator": dict(topic_starts),
    }


def _empty_result(persons):
    return {
        "instantReplyRate": {p: 0 for p in persons},
        "avgReplyTime": {p: 0 for p in persons},
        "speedDistribution": {"under1min": 0, "1to5min": 0, "5to30min": 0, "30to60min": 0, "over60min": 0},
        "topicInitiator": {},
    }
```

**Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_reply_analysis.py -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add backend/app/services/reply_analysis.py backend/tests/test_reply_analysis.py
git commit -m "feat: implement reply behavior analysis with speed distribution"
```

---

### Task 5: Time Patterns Analysis

**Files:**
- Create: `backend/app/services/time_patterns.py`
- Create: `backend/tests/test_time_patterns.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_time_patterns.py
from pathlib import Path
from app.services.parser import parse_line_chat
from app.services.time_patterns import compute_time_patterns

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


def _parsed():
    return parse_line_chat(FIXTURE.read_text(encoding="utf-8"))


def test_heatmap_shape():
    result = compute_time_patterns(_parsed())
    heatmap = result["heatmap"]
    # 7 days x 8 time slots (3-hour blocks)
    assert len(heatmap) == 7
    assert all(len(row) == 8 for row in heatmap)


def test_heatmap_has_values():
    result = compute_time_patterns(_parsed())
    total = sum(sum(row) for row in result["heatmap"])
    assert total > 0


def test_monthly_trend():
    result = compute_time_patterns(_parsed())
    trend = result["trend"]
    assert len(trend) > 0
    first = trend[0]
    assert "period" in first
    for person in _parsed()["persons"]:
        assert person in first


def test_goodnight_analysis():
    result = compute_time_patterns(_parsed())
    gn = result["goodnightAnalysis"]
    assert "whoSaysGoodnightFirst" in gn
    assert "whoSaysGoodmorningFirst" in gn
    assert "avgLastChatTime" in gn
```

Run: `cd backend && python -m pytest tests/test_time_patterns.py -v`
Expected: FAIL

**Step 2: Implement time patterns**

```python
# backend/app/services/time_patterns.py
import re
from collections import defaultdict
from datetime import datetime
from app.services.parser import Message


GOODNIGHT_RE = re.compile(r"(晚安|good\s*night|gn|拜拜|掰掰|睡了|想睡)", re.IGNORECASE)
GOODMORNING_RE = re.compile(r"(早安|早～|早啊|good\s*morning|gm|起床)", re.IGNORECASE)


def compute_time_patterns(parsed: dict) -> dict:
    messages: list[Message] = parsed["messages"]
    persons: list[str] = parsed["persons"]

    heatmap = _build_heatmap(messages)
    trend = _build_trend(messages, persons)
    goodnight = _build_goodnight(messages, persons)

    return {
        "heatmap": heatmap,
        "trend": trend,
        "goodnightAnalysis": goodnight,
    }


def _build_heatmap(messages: list[Message]) -> list[list[int]]:
    """7 rows (Mon=0..Sun=6) x 8 cols (0-3, 3-6, ..., 21-24)"""
    grid = [[0] * 8 for _ in range(7)]
    for m in messages:
        day = m.timestamp.weekday()  # 0=Mon
        slot = m.timestamp.hour // 3  # 0-7
        grid[day][slot] += 1
    return grid


def _build_trend(messages: list[Message], persons: list[str]) -> list[dict]:
    """Monthly message counts per person."""
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {p: 0 for p in persons})
    for m in messages:
        key = m.timestamp.strftime("%Y-%m")
        buckets[key][m.sender] += 1

    result = []
    for period in sorted(buckets):
        entry = {"period": period, **buckets[period]}
        result.append(entry)
    return result


def _build_goodnight(messages: list[Message], persons: list[str]) -> dict:
    gn_first: dict[str, int] = defaultdict(int)
    gm_first: dict[str, int] = defaultdict(int)
    last_chat_hours: list[float] = []

    # Group messages by date
    by_date: dict[str, list[Message]] = defaultdict(list)
    for m in messages:
        by_date[str(m.timestamp.date())].append(m)

    for date_str, day_msgs in by_date.items():
        # Find first goodnight
        for m in day_msgs:
            if m.msg_type == "text" and GOODNIGHT_RE.search(m.content):
                gn_first[m.sender] += 1
                break

        # Find first good morning
        for m in day_msgs:
            if m.msg_type == "text" and GOODMORNING_RE.search(m.content):
                gm_first[m.sender] += 1
                break

        # Last message time of day
        if day_msgs:
            last = day_msgs[-1].timestamp
            last_chat_hours.append(last.hour + last.minute / 60)

    avg_last = round(sum(last_chat_hours) / len(last_chat_hours), 1) if last_chat_hours else 0

    return {
        "whoSaysGoodnightFirst": dict(gn_first),
        "whoSaysGoodmorningFirst": dict(gm_first),
        "avgLastChatTime": avg_last,
    }
```

**Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_time_patterns.py -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add backend/app/services/time_patterns.py backend/tests/test_time_patterns.py
git commit -m "feat: implement time patterns with heatmap, trends, and goodnight analysis"
```

---

### Task 6: Cold War Detection

**Files:**
- Create: `backend/app/services/cold_war.py`
- Create: `backend/tests/test_cold_war.py`
- Modify: `backend/tests/fixtures/` — add a fixture with cold war pattern

**Step 1: Create extended fixture**

```text
# backend/tests/fixtures/sample_chat_coldwar.txt
[LINE] 與小美的聊天記錄
儲存日期：2025/02/10 14:00

2024/03/14（四）
09:00	小美	早安
09:01	阿明	早安！
12:00	小美	午安～
12:01	阿明	午安！今天忙嗎
18:00	小美	下班了
18:01	阿明	走！去吃飯
22:00	小美	晚安
22:01	阿明	晚安～
2024/03/15（五）
20:00	小美	...
2024/03/16（六）
15:00	阿明	在幹嘛
2024/03/17（日）
10:00	小美	嗯
18:00	阿明	我們出來聊聊好嗎
2024/03/18（一）
09:00	小美	好
09:01	阿明	太好了
09:05	小美	那中午見
09:06	阿明	好！
12:00	小美	到了～
12:01	阿明	我也到了！
18:00	小美	今天謝謝你
18:01	阿明	應該的，晚安
18:02	小美	晚安～
```

**Step 2: Write failing tests**

```python
# backend/tests/test_cold_war.py
from pathlib import Path
from app.services.parser import parse_line_chat
from app.services.cold_war import detect_cold_wars

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat_coldwar.txt"


def _parsed():
    return parse_line_chat(FIXTURE.read_text(encoding="utf-8"))


def test_detects_cold_war_period():
    result = detect_cold_wars(_parsed())
    assert len(result) >= 1


def test_cold_war_has_dates():
    result = detect_cold_wars(_parsed())
    event = result[0]
    assert "startDate" in event
    assert "endDate" in event
    assert "messageDrop" in event


def test_cold_war_dates_are_mid_march():
    result = detect_cold_wars(_parsed())
    event = result[0]
    assert "2024-03-15" <= event["startDate"] <= "2024-03-17"
```

Run: `cd backend && python -m pytest tests/test_cold_war.py -v`
Expected: FAIL

**Step 3: Implement cold war detection**

```python
# backend/app/services/cold_war.py
from collections import defaultdict
from app.services.parser import Message


def detect_cold_wars(parsed: dict, drop_threshold: float = 0.5) -> list[dict]:
    """Detect periods where message volume drops significantly."""
    messages: list[Message] = parsed["messages"]
    if not messages:
        return []

    # Daily message counts
    daily: dict[str, int] = defaultdict(int)
    for m in messages:
        daily[str(m.timestamp.date())] += 1

    dates = sorted(daily.keys())
    if len(dates) < 5:
        return []

    # Compute 7-day rolling average
    counts = [daily.get(d, 0) for d in dates]
    window = min(7, len(counts))
    rolling_avg = sum(counts[:window]) / window

    cold_wars = []
    in_cold_war = False
    cw_start = None

    for i, d in enumerate(dates):
        count = counts[i]

        # Update rolling avg (simple moving)
        start_idx = max(0, i - window)
        rolling_avg = sum(counts[start_idx:i + 1]) / (i - start_idx + 1)

        # Check for significant drop
        baseline = sum(counts[max(0, i - 14):max(1, i)]) / max(1, min(14, i))
        is_low = count <= max(baseline * (1 - drop_threshold), 1) if baseline > 2 else False

        if is_low and not in_cold_war:
            in_cold_war = True
            cw_start = d
        elif not is_low and in_cold_war:
            in_cold_war = False
            cold_wars.append({
                "startDate": cw_start,
                "endDate": dates[i - 1] if i > 0 else d,
                "messageDrop": round((1 - count / max(baseline, 1)) * 100, 1),
            })

    if in_cold_war and cw_start:
        cold_wars.append({
            "startDate": cw_start,
            "endDate": dates[-1],
            "messageDrop": 0,
        })

    return cold_wars
```

**Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_cold_war.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/services/cold_war.py backend/tests/test_cold_war.py backend/tests/fixtures/sample_chat_coldwar.txt
git commit -m "feat: implement cold war detection based on message volume drops"
```

---

### Task 7: Text Analysis (Word Frequency + Unique Phrases)

**Files:**
- Create: `backend/app/services/text_analysis.py`
- Create: `backend/tests/test_text_analysis.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_text_analysis.py
from pathlib import Path
from app.services.parser import parse_line_chat
from app.services.text_analysis import compute_text_analysis

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chat.txt"


def _parsed():
    return parse_line_chat(FIXTURE.read_text(encoding="utf-8"))


def test_word_cloud_per_person():
    result = compute_text_analysis(_parsed())
    wc = result["wordCloud"]
    persons = _parsed()["persons"]
    for p in persons:
        assert p in wc
        # Each person has a list of {word, count}
        assert isinstance(wc[p], list)


def test_word_cloud_has_words():
    result = compute_text_analysis(_parsed())
    wc = result["wordCloud"]
    # At least one person should have some words
    has_words = any(len(wc[p]) > 0 for p in wc)
    assert has_words


def test_unique_phrases():
    result = compute_text_analysis(_parsed())
    up = result["uniquePhrases"]
    assert isinstance(up, list)
```

Run: `cd backend && python -m pytest tests/test_text_analysis.py -v`
Expected: FAIL

**Step 2: Implement text analysis**

```python
# backend/app/services/text_analysis.py
import re
from collections import Counter
from app.services.parser import Message

import jieba

# Common Chinese stop words
STOP_WORDS = {
    "的", "了", "是", "我", "你", "他", "她", "在", "有", "也", "不",
    "就", "都", "好", "嗎", "呢", "吧", "啊", "喔", "哦", "欸",
    "這", "那", "會", "要", "跟", "和", "但", "可以", "什麼", "沒有",
    "一個", "很", "還", "被", "把", "到", "說",
}


def compute_text_analysis(parsed: dict) -> dict:
    messages: list[Message] = parsed["messages"]
    persons: list[str] = parsed["persons"]

    word_cloud = {}
    all_words_by_person: dict[str, Counter] = {}

    for p in persons:
        texts = [m.content for m in messages if m.sender == p and m.msg_type == "text"]
        combined = " ".join(texts)
        words = jieba.lcut(combined)
        # Filter: length >= 2, not stop words, not pure punctuation/numbers
        filtered = [
            w for w in words
            if len(w) >= 2
            and w not in STOP_WORDS
            and not re.match(r"^[\d\W]+$", w)
        ]
        counter = Counter(filtered)
        all_words_by_person[p] = counter
        word_cloud[p] = [
            {"word": w, "count": c}
            for w, c in counter.most_common(80)
        ]

    # Unique phrases: words that appear disproportionately in THIS chat
    # Simple approach: words used by both persons (shared vocabulary)
    if len(persons) == 2:
        p1, p2 = persons
        shared = set(all_words_by_person[p1]) & set(all_words_by_person[p2])
        unique = sorted(
            shared,
            key=lambda w: all_words_by_person[p1][w] + all_words_by_person[p2][w],
            reverse=True,
        )[:20]
        unique_phrases = [
            {
                "phrase": w,
                "count": all_words_by_person[p1][w] + all_words_by_person[p2][w],
            }
            for w in unique
        ]
    else:
        unique_phrases = []

    return {
        "wordCloud": word_cloud,
        "uniquePhrases": unique_phrases,
    }
```

**Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_text_analysis.py -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add backend/app/services/text_analysis.py backend/tests/test_text_analysis.py
git commit -m "feat: implement text analysis with jieba word cloud and unique phrases"
```

---

### Task 8: Encryption Utilities

**Files:**
- Create: `backend/app/services/encryption.py`
- Create: `backend/tests/test_encryption.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_encryption.py
import base64
import os
from app.services.encryption import decrypt_aes_gcm, encrypt_aes_gcm


def test_encrypt_decrypt_roundtrip():
    key = os.urandom(32)
    plaintext = "Hello, 你好！這是測試訊息。".encode("utf-8")

    encrypted = encrypt_aes_gcm(plaintext, key)
    decrypted = decrypt_aes_gcm(encrypted, key)

    assert decrypted == plaintext


def test_decrypt_with_base64_key():
    key = os.urandom(32)
    key_b64 = base64.b64encode(key).decode()
    plaintext = "測試".encode("utf-8")

    encrypted = encrypt_aes_gcm(plaintext, key)
    key_decoded = base64.b64decode(key_b64)
    decrypted = decrypt_aes_gcm(encrypted, key_decoded)

    assert decrypted == plaintext


def test_wrong_key_fails():
    key = os.urandom(32)
    wrong_key = os.urandom(32)
    plaintext = b"secret"

    encrypted = encrypt_aes_gcm(plaintext, key)

    try:
        decrypt_aes_gcm(encrypted, wrong_key)
        assert False, "Should have raised"
    except Exception:
        pass
```

Run: `cd backend && python -m pytest tests/test_encryption.py -v`
Expected: FAIL

**Step 2: Implement encryption**

```python
# backend/app/services/encryption.py
from Crypto.Cipher import AES


def encrypt_aes_gcm(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt with AES-256-GCM. Returns nonce(12) + ciphertext + tag(16)."""
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce + ciphertext + tag


def decrypt_aes_gcm(data: bytes, key: bytes) -> bytes:
    """Decrypt AES-256-GCM. Expects nonce(12) + ciphertext + tag(16)."""
    nonce = data[:12]
    tag = data[-16:]
    ciphertext = data[12:-16]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)
```

**Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_encryption.py -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add backend/app/services/encryption.py backend/tests/test_encryption.py
git commit -m "feat: implement AES-256-GCM encryption/decryption utilities"
```

---

### Task 9: Claude API — AI Analysis Service

**Files:**
- Create: `backend/app/services/ai_analysis.py`
- Create: `backend/tests/test_ai_analysis.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_ai_analysis.py
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
```

Run: `cd backend && python -m pytest tests/test_ai_analysis.py -v`
Expected: FAIL

**Step 2: Implement AI analysis**

```python
# backend/app/services/ai_analysis.py
import json
import os
from collections import defaultdict
from datetime import datetime

from app.services.parser import Message

# Lazy import anthropic to allow tests without API key
_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic()
    return _client


def sample_messages(
    messages: list[Message], per_day: int = 8
) -> list[Message]:
    """Sample representative messages per day to reduce API cost."""
    if not messages:
        return []

    by_day: dict[str, list[Message]] = defaultdict(list)
    for m in messages:
        if m.msg_type == "text":
            by_day[str(m.timestamp.date())].append(m)

    sampled = []
    for day in sorted(by_day):
        day_msgs = by_day[day]
        if len(day_msgs) <= per_day:
            sampled.extend(day_msgs)
        else:
            step = len(day_msgs) / per_day
            sampled.extend(day_msgs[int(i * step)] for i in range(per_day))

    return sampled


def build_prompt(messages: list[Message], persons: list[str]) -> str:
    lines = []
    for m in messages:
        lines.append(f"[{m.timestamp.strftime('%Y-%m-%d %H:%M')}] {m.sender}: {m.content}")

    conversation = "\n".join(lines)
    p1, p2 = persons[0], persons[1] if len(persons) > 1 else "Person2"

    return f"""你是一位專業的聊天對話分析師。請分析以下 {p1} 和 {p2} 之間的對話摘錄，回傳 JSON 格式結果。

對話摘錄：
{conversation}

請回傳以下 JSON（不要加 markdown code block）：
{{
  "loveScore": {{
    "score": <0-100 的整數，代表兩人的心動/互動指數>,
    "comment": "<一段 50 字以內的中文整體評語>"
  }},
  "sentiment": {{
    "sweet": <甜蜜訊息佔比 0-100>,
    "flirty": <曖昧/調情佔比 0-100>,
    "daily": <日常分享佔比 0-100>,
    "conflict": <爭吵/不滿佔比 0-100>,
    "missing": <思念佔比 0-100>
  }},
  "goldenQuotes": {{
    "sweetest": [
      {{"quote": "<原文>", "sender": "<發送者>", "date": "<日期>"}},
    ],
    "funniest": [
      {{"quote": "<原文>", "sender": "<發送者>", "date": "<日期>"}}
    ],
    "mostTouching": [
      {{"quote": "<原文>", "sender": "<發送者>", "date": "<日期>"}}
    ]
  }},
  "insight": "<一段 100 字以內的中文深度洞察，描述兩人的互動模式和關係特色>"
}}"""


async def analyze_with_ai(
    messages: list[Message], persons: list[str]
) -> dict:
    """Call Claude API for sentiment analysis and golden quotes."""
    sampled = sample_messages(messages)
    if not sampled:
        return _fallback_result()

    prompt = build_prompt(sampled, persons)
    client = _get_client()

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    # Try to parse JSON from response
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        if "```" in text:
            json_str = text.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            return json.loads(json_str.strip())
        return _fallback_result()


def _fallback_result() -> dict:
    return {
        "loveScore": {"score": 50, "comment": "資料不足，無法完整分析"},
        "sentiment": {"sweet": 20, "flirty": 20, "daily": 40, "conflict": 10, "missing": 10},
        "goldenQuotes": {"sweetest": [], "funniest": [], "mostTouching": []},
        "insight": "對話內容不足，建議上傳更長的對話記錄以獲得更準確的分析。",
    }
```

**Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_ai_analysis.py -v`
Expected: ALL PASS (tests only test sampling and prompt building, not API calls)

**Step 4: Commit**

```bash
git add backend/app/services/ai_analysis.py backend/tests/test_ai_analysis.py
git commit -m "feat: implement AI analysis service with message sampling and Claude API"
```

---

### Task 10: Backend API Endpoint — POST /api/analyze

**Files:**
- Create: `backend/app/routers/analyze.py`
- Modify: `backend/app/main.py` — register router
- Create: `backend/tests/test_api_analyze.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_api_analyze.py
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
        data={"key": base64.b64encode(key).decode()},
        files={"file": ("chat.txt.enc", encrypted, "application/octet-stream")},
    )
    assert resp.status_code == 200


async def test_analyze_returns_basic_stats(client):
    key = os.urandom(32)
    plaintext = FIXTURE.read_bytes()
    encrypted = encrypt_aes_gcm(plaintext, key)

    resp = await client.post(
        "/api/analyze",
        data={"key": base64.b64encode(key).decode()},
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
        data={"key": base64.b64encode(wrong_key).decode()},
        files={"file": ("chat.txt.enc", encrypted, "application/octet-stream")},
    )
    assert resp.status_code == 400
```

Run: `cd backend && python -m pytest tests/test_api_analyze.py -v`
Expected: FAIL

**Step 2: Implement analyze endpoint**

```python
# backend/app/routers/analyze.py
import base64

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.cold_war import detect_cold_wars
from app.services.encryption import decrypt_aes_gcm
from app.services.parser import parse_line_chat
from app.services.reply_analysis import compute_reply_behavior
from app.services.stats import compute_basic_stats
from app.services.text_analysis import compute_text_analysis
from app.services.time_patterns import compute_time_patterns

router = APIRouter(prefix="/api")


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    key: str = Form(...),
    skip_ai: bool = Form(default=False),
):
    # Decrypt
    try:
        raw_key = base64.b64decode(key)
        encrypted_data = await file.read()
        plaintext = decrypt_aes_gcm(encrypted_data, raw_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Decryption failed")

    # Parse
    try:
        text = plaintext.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding")
    finally:
        # Clear plaintext bytes from memory
        plaintext = b""

    parsed = parse_line_chat(text)
    if not parsed["messages"]:
        raise HTTPException(status_code=400, detail="No messages found in file")

    # Run all analysis
    basic_stats = compute_basic_stats(parsed)
    reply_behavior = compute_reply_behavior(parsed)
    time_patterns = compute_time_patterns(parsed)
    cold_wars = detect_cold_wars(parsed)
    text_analysis = compute_text_analysis(parsed)

    # AI analysis (optional, skip in tests)
    ai_result = None
    if not skip_ai:
        try:
            from app.services.ai_analysis import analyze_with_ai
            ai_result = await analyze_with_ai(parsed["messages"], parsed["persons"])
        except Exception:
            ai_result = None

    # Clear raw text from memory
    text = ""
    parsed = {}

    result = {
        "persons": basic_stats["dateRange"] and parsed.get("persons", basic_stats["personBalance"].get("messages", {}).keys()),
        "basicStats": basic_stats,
        "replyBehavior": reply_behavior,
        "timePatterns": time_patterns,
        "coldWars": cold_wars,
        "textAnalysis": text_analysis,
    }

    if ai_result:
        result["aiAnalysis"] = ai_result

    return result
```

Wait — there's a bug above: we clear `parsed` before using `parsed["persons"]`. Fix:

```python
# backend/app/routers/analyze.py
import base64

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.cold_war import detect_cold_wars
from app.services.encryption import decrypt_aes_gcm
from app.services.parser import parse_line_chat
from app.services.reply_analysis import compute_reply_behavior
from app.services.stats import compute_basic_stats
from app.services.text_analysis import compute_text_analysis
from app.services.time_patterns import compute_time_patterns

router = APIRouter(prefix="/api")


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    key: str = Form(...),
    skip_ai: bool = Form(default=False),
):
    # Decrypt
    try:
        raw_key = base64.b64decode(key)
        encrypted_data = await file.read()
        plaintext = decrypt_aes_gcm(encrypted_data, raw_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Decryption failed")

    # Parse
    try:
        text = plaintext.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding")
    finally:
        plaintext = b""

    parsed = parse_line_chat(text)
    text = ""  # Clear raw text

    if not parsed["messages"]:
        raise HTTPException(status_code=400, detail="No messages found in file")

    persons = parsed["persons"]

    # Run all local analysis
    basic_stats = compute_basic_stats(parsed)
    reply_behavior = compute_reply_behavior(parsed)
    time_patterns = compute_time_patterns(parsed)
    cold_wars = detect_cold_wars(parsed)
    text_analysis = compute_text_analysis(parsed)

    # AI analysis (optional)
    ai_result = None
    if not skip_ai:
        try:
            from app.services.ai_analysis import analyze_with_ai
            ai_result = await analyze_with_ai(parsed["messages"], persons)
        except Exception:
            ai_result = None

    # Clear parsed data
    parsed = {}

    result = {
        "persons": persons,
        "basicStats": basic_stats,
        "replyBehavior": reply_behavior,
        "timePatterns": time_patterns,
        "coldWars": cold_wars,
        "textAnalysis": text_analysis,
    }

    if ai_result:
        result["aiAnalysis"] = ai_result

    return result
```

**Step 3: Register router in main.py**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.analyze import router as analyze_router

app = FastAPI(title="CupidNow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

**Step 4: Update test to use skip_ai**

Update the test to add `skip_ai=true` to avoid needing a Claude API key:

```python
# In test_api_analyze.py, update the data dict in each test:
data={"key": base64.b64encode(key).decode(), "skip_ai": "true"},
```

**Step 5: Run tests**

Run: `cd backend && python -m pytest tests/test_api_analyze.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add backend/app/routers/ backend/app/main.py backend/tests/test_api_analyze.py
git commit -m "feat: implement POST /api/analyze endpoint with full analysis pipeline"
```

---

### Task 11: Frontend Project Scaffold

**Files:**
- Create: `frontend/` — Vite + React + TypeScript project
- Create: `frontend/src/lib/theme.ts` — Design tokens
- Create: `frontend/src/lib/encryption.ts` — AES encryption

**Step 1: Scaffold with Vite**

```bash
cd /Users/dogdogman/Documents/CupidNow
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install recharts react-router-dom
npm install html2canvas  # for share card generation
```

**Step 2: Configure Tailwind v4**

```css
/* frontend/src/index.css */
@import "tailwindcss";

@theme {
  --color-rose-primary: #E8457E;
  --color-rose-dark: #C4225D;
  --color-rose-light: #FDDEE8;
  --color-rose-soft: #E8457E18;
  --color-purple-accent: #9F7AEA;
  --color-purple-soft: #9F7AEA20;
  --color-gold-accent: #F5A623;
  --color-teal-positive: #38B2AC;
  --color-coral-warm: #FF7E7E;
  --color-bg-page: #FFF8FA;
  --color-bg-card: #FFFFFF;
  --color-bg-blush: #FFF0F3;
  --color-bg-hero-dark: #2D1B33;
  --color-text-primary: #2D1F3D;
  --color-text-secondary: #7A6B8A;
  --color-text-muted: #B8ADC7;
  --color-border-light: #F3E8EE;
  --font-heading: "Plus Jakarta Sans", sans-serif;
  --font-body: "Inter", sans-serif;
}
```

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

**Step 3: Create encryption utility**

```typescript
// frontend/src/lib/encryption.ts
export async function encryptFile(file: File): Promise<{ encrypted: ArrayBuffer; key: string }> {
  const key = crypto.getRandomValues(new Uint8Array(32));
  const iv = crypto.getRandomValues(new Uint8Array(12));

  const cryptoKey = await crypto.subtle.importKey(
    "raw", key, "AES-GCM", false, ["encrypt"]
  );

  const fileBuffer = await file.arrayBuffer();
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv }, cryptoKey, fileBuffer
  );

  // Format: nonce(12) + ciphertext + tag (WebCrypto appends tag automatically)
  const result = new Uint8Array(iv.length + ciphertext.byteLength);
  result.set(iv, 0);
  result.set(new Uint8Array(ciphertext), iv.length);

  const keyB64 = btoa(String.fromCharCode(...key));

  return { encrypted: result.buffer, key: keyB64 };
}
```

**Step 4: Create TypeScript types**

```typescript
// frontend/src/types/analysis.ts
export interface AnalysisResult {
  persons: string[];
  basicStats: BasicStats;
  replyBehavior: ReplyBehavior;
  timePatterns: TimePatterns;
  coldWars: ColdWarEvent[];
  textAnalysis: TextAnalysis;
  aiAnalysis?: AIAnalysis;
}

export interface BasicStats {
  messageCount: Record<string, number>;
  wordCount: Record<string, number>;
  typeBreakdown: Record<string, number>;
  callStats: {
    totalCalls: number;
    completedCalls: number;
    missedCalls: number;
    totalDurationSeconds: number;
    avgDurationSeconds: number;
    maxDurationSeconds: number;
  };
  dateRange: { start: string; end: string; totalDays: number };
  personBalance: Record<string, Record<string, { count: number; percent: number }>>;
}

export interface ReplyBehavior {
  instantReplyRate: Record<string, number>;
  avgReplyTime: Record<string, number>;
  speedDistribution: Record<string, number>;
  topicInitiator: Record<string, number>;
}

export interface TimePatterns {
  heatmap: number[][];
  trend: Array<Record<string, string | number>>;
  goodnightAnalysis: {
    whoSaysGoodnightFirst: Record<string, number>;
    whoSaysGoodmorningFirst: Record<string, number>;
    avgLastChatTime: number;
  };
}

export interface ColdWarEvent {
  startDate: string;
  endDate: string;
  messageDrop: number;
}

export interface TextAnalysis {
  wordCloud: Record<string, Array<{ word: string; count: number }>>;
  uniquePhrases: Array<{ phrase: string; count: number }>;
}

export interface AIAnalysis {
  loveScore: { score: number; comment: string };
  sentiment: Record<string, number>;
  goldenQuotes: {
    sweetest: Quote[];
    funniest: Quote[];
    mostTouching: Quote[];
  };
  insight: string;
}

interface Quote {
  quote: string;
  sender: string;
  date: string;
}
```

**Step 5: Verify build**

```bash
cd frontend && npm run build
```
Expected: Build succeeds

**Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold frontend with React, Vite, Tailwind v4, and design tokens"
```

---

### Task 12: Frontend — Upload Page

**Files:**
- Create: `frontend/src/pages/UploadPage.tsx`
- Create: `frontend/src/components/FileDropzone.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create FileDropzone component**

Reference: Landing page design in `designs/cupidnow-ui.pen` node `JaWr8` — upload area with dashed border, gradient CTA button, drag-and-drop support.

```tsx
// frontend/src/components/FileDropzone.tsx
import { useCallback, useState } from "react";

interface Props {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export function FileDropzone({ onFileSelected, disabled }: Props) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file?.name.endsWith(".txt")) onFileSelected(file);
    },
    [onFileSelected]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelected(file);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`
        flex flex-col items-center gap-4 rounded-3xl border-2 border-dashed p-12
        transition-colors duration-200
        ${isDragging ? "border-rose-primary bg-rose-soft" : "border-border-light bg-white"}
        ${disabled ? "opacity-50 pointer-events-none" : ""}
      `}
    >
      <div className="text-4xl">💌</div>
      <p className="font-heading text-lg font-bold text-text-primary">
        拖放或點擊上傳 LINE 對話記錄
      </p>
      <p className="text-sm text-text-secondary">
        支援 .txt 格式的 LINE 聊天記錄匯出檔
      </p>
      <label className="cursor-pointer rounded-xl bg-gradient-to-r from-rose-primary to-purple-accent px-8 py-3 font-body text-base font-semibold text-white shadow-lg transition hover:opacity-90">
        選擇檔案
        <input
          type="file"
          accept=".txt"
          onChange={handleChange}
          className="hidden"
          disabled={disabled}
        />
      </label>
    </div>
  );
}
```

**Step 2: Create UploadPage**

```tsx
// frontend/src/pages/UploadPage.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileDropzone } from "../components/FileDropzone";
import { encryptFile } from "../lib/encryption";
import type { AnalysisResult } from "../types/analysis";

interface Props {
  onResult: (result: AnalysisResult) => void;
}

const LOADING_TEXTS = [
  "正在解讀你們的故事...",
  "計算心動的瞬間...",
  "分析互動指數...",
  "尋找最甜蜜的對話...",
];

export function UploadPage({ onResult }: Props) {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleFile = async (file: File) => {
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      // Encrypt
      setProgress(10);
      const { encrypted, key } = await encryptFile(file);

      // Upload
      setProgress(30);
      const formData = new FormData();
      formData.append("file", new Blob([encrypted]), "chat.txt.enc");
      formData.append("key", key);

      const resp = await fetch("/api/analyze", { method: "POST", body: formData });

      setProgress(90);
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "分析失敗" }));
        throw new Error(err.detail || "分析失敗");
      }

      const result: AnalysisResult = await resp.json();
      setProgress(100);
      onResult(result);
      navigate("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "發生未知錯誤");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-page">
      {/* Header */}
      <header className="flex items-center justify-between px-20 py-5">
        <span className="font-heading text-2xl font-extrabold text-text-primary">
          💕 CupidNow
        </span>
      </header>

      {/* Hero */}
      <main className="mx-auto flex max-w-2xl flex-col items-center gap-8 px-4 pt-16">
        <span className="rounded-full bg-rose-soft px-4 py-1 text-sm font-semibold text-rose-primary">
          Powered by AI Analysis
        </span>
        <h1 className="text-center font-heading text-5xl font-extrabold leading-tight text-text-primary">
          用數據，看見心動的溫度
        </h1>
        <p className="text-center text-lg text-text-secondary">
          上傳 LINE 對話記錄，AI 幫你解讀曖昧到心動的每個瞬間
        </p>

        {loading ? (
          <div className="flex w-full max-w-md flex-col items-center gap-4 rounded-3xl border border-border-light bg-white p-12">
            <div className="h-2 w-full overflow-hidden rounded-full bg-rose-soft">
              <div
                className="h-full rounded-full bg-gradient-to-r from-rose-primary to-purple-accent transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="animate-pulse text-sm text-text-secondary">
              {LOADING_TEXTS[Math.floor((progress / 100) * LOADING_TEXTS.length) % LOADING_TEXTS.length]}
            </p>
          </div>
        ) : (
          <FileDropzone onFileSelected={handleFile} />
        )}

        {error && (
          <p className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-600">{error}</p>
        )}

        {/* Privacy badges */}
        <div className="flex flex-wrap justify-center gap-4 pt-8">
          {["🔒 AES-256 加密傳輸", "🗑️ 分析完即刪除", "🚫 不儲存任何明文", "👤 無需註冊帳號"].map((t) => (
            <span key={t} className="rounded-full border border-border-light bg-white px-4 py-2 text-sm font-semibold text-text-primary">
              {t}
            </span>
          ))}
        </div>
      </main>
    </div>
  );
}
```

**Step 3: Set up App routing**

```tsx
// frontend/src/App.tsx
import { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { UploadPage } from "./pages/UploadPage";
import type { AnalysisResult } from "./types/analysis";

export default function App() {
  const [result, setResult] = useState<AnalysisResult | null>(null);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage onResult={setResult} />} />
        <Route path="/dashboard" element={
          result ? <div>Dashboard placeholder</div> : <div>No data</div>
        } />
      </Routes>
    </BrowserRouter>
  );
}
```

**Step 4: Verify build**

```bash
cd frontend && npm run build
```
Expected: Build succeeds

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: implement upload page with file encryption and drag-and-drop"
```

---

### Task 13: Frontend — Dashboard Page (Structure + Hero + Stats)

**Files:**
- Create: `frontend/src/pages/DashboardPage.tsx`
- Create: `frontend/src/components/dashboard/LoveScoreHero.tsx`
- Create: `frontend/src/components/dashboard/BasicStatsCards.tsx`
- Create: `frontend/src/components/dashboard/PersonBalance.tsx`
- Modify: `frontend/src/App.tsx`

Reference: Dashboard design in `designs/cupidnow-ui.pen` node `Ym86K`.

These are the top-section components. Each component matches a section of the mockup. Implementation follows the exact design tokens and layout from the .pen file.

Code for each component should follow the mockup exactly. Components receive the `AnalysisResult` as props and render the data. Use Recharts for charts.

**Step 1: Build all components**

Build `LoveScoreHero`, `BasicStatsCards`, and `PersonBalance` as separate components. `DashboardPage` composes them.

**Step 2: Wire up in App.tsx**

Replace the placeholder route with `<DashboardPage result={result} />`.

**Step 3: Verify build + visual check**

```bash
cd frontend && npm run build
```

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: implement dashboard hero, basic stats, and person balance sections"
```

---

### Task 14: Frontend — Reply Behavior + Time Patterns Charts

**Files:**
- Create: `frontend/src/components/dashboard/ReplyBehavior.tsx`
- Create: `frontend/src/components/dashboard/TimeHeatmap.tsx`
- Create: `frontend/src/components/dashboard/TrendChart.tsx`

Reference: Dashboard design — Reply Behavior section (node `TQtNz`), Time Patterns section (node `rjorn`).

- `ReplyBehavior`: Instant reply rate bars, speed distribution bar chart (Recharts BarChart), fun stats cards
- `TimeHeatmap`: 7×8 grid with color intensity based on message count. Chinese day labels, time range headers, legend gradient
- `TrendChart`: Bi-monthly or monthly grouped bar chart (Recharts BarChart) with pink/purple bars, day/week/month tab switcher

**Step 1: Implement components with Recharts**

**Step 2: Verify build**

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: implement reply behavior and time pattern chart components"
```

---

### Task 15: Frontend — Goodnight, Cold War, Sentiment, Word Cloud, Golden Quotes

**Files:**
- Create: `frontend/src/components/dashboard/GoodnightAnalysis.tsx`
- Create: `frontend/src/components/dashboard/ColdWarTimeline.tsx`
- Create: `frontend/src/components/dashboard/SentimentAnalysis.tsx`
- Create: `frontend/src/components/dashboard/WordCloud.tsx`
- Create: `frontend/src/components/dashboard/GoldenQuotes.tsx`
- Create: `frontend/src/components/dashboard/ShareCTA.tsx`

Reference: Dashboard design sections — `BOqto`, `Buchz`, `b0pkg`, `DHJ2C`, `GopYD`, `gZduJ`.

Each component matches its mockup section. Key notes:
- `GoodnightAnalysis`: 4 dark-themed stat cards
- `ColdWarTimeline`: Vertical timeline with event cards
- `SentimentAnalysis`: Horizontal bar chart (Recharts) + AI insight gradient card
- `WordCloud`: Simple word frequency display (sized text elements). For MVP, no actual cloud shape — just sized words
- `GoldenQuotes`: 3 quote cards with tags (sweetest/funniest/most touching)
- `ShareCTA`: Gradient share button + download button. Uses `html2canvas` to capture dashboard summary as image

**Step 1: Implement all components**

**Step 2: Integrate into DashboardPage**

**Step 3: Verify build**

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: implement remaining dashboard sections"
```

---

### Task 16: End-to-End Integration Test

**Files:**
- Create: `backend/tests/test_integration.py`

**Step 1: Write integration test**

```python
# backend/tests/test_integration.py
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
```

**Step 2: Run full test suite**

Run: `cd backend && python -m pytest -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "test: add end-to-end integration test for full analysis pipeline"
```

---

### Task 17: Dev Server Setup & Manual Testing

**Step 1: Run backend**

```bash
cd backend && uvicorn app.main:app --reload --port 8000
```

**Step 2: Run frontend (separate terminal)**

```bash
cd frontend && npm run dev
```

**Step 3: Manual test with a real LINE export file**

1. Open http://localhost:5173
2. Upload a real LINE txt export file
3. Verify the upload encrypts and sends to backend
4. Verify the dashboard renders with real data

**Step 4: Fix any issues found during manual testing**

**Step 5: Commit any fixes**

```bash
git add -A
git commit -m "fix: address issues found during manual testing"
```

---

## Phase 2 — Enhancements (After MVP)

### Task 18: SSE Progress Streaming

Replace the simple POST response with SSE (Server-Sent Events) so the frontend can show real-time progress during analysis. Use `sse-starlette` on the backend and `EventSource` on the frontend.

### Task 19: Share Card Generation

Implement `html2canvas` capture of a summary card. The share card should include: love score, total messages, date range, top stats. Style it as a beautiful social media card.

### Task 20: UI Animations & Polish

Add smooth transitions, number count-up animations on the love score, and parallax scroll effects between dashboard sections. Add the loading text carousel during analysis.

### Task 21: Mobile Responsive

Ensure all dashboard sections stack properly on mobile. Test at 375px, 768px, 1024px, 1440px widths.

---

## Execution Checklist

| # | Task | Status |
|---|------|--------|
| 1 | Backend scaffold | ✅ |
| 2 | LINE txt parser | ✅ |
| 3 | Basic stats engine | ✅ |
| 4 | Reply behavior analysis | ✅ |
| 5 | Time patterns analysis | ✅ |
| 6 | Cold war detection | ✅ |
| 7 | Text analysis (word cloud) | ✅ |
| 8 | Encryption utilities | ✅ (保留但 API 不再使用加密) |
| 9 | Claude API integration | ✅ |
| 10 | API endpoint | ✅ (移除加密，新增速率限制/檔案大小限制) |
| 11 | Frontend scaffold | ✅ |
| 12 | Upload page | ✅ (移除前端加密) |
| 13 | Dashboard: hero + stats + balance | ✅ |
| 14 | Dashboard: reply + time charts | ✅ (CSS 圖表取代 Recharts) |
| 15 | Dashboard: remaining sections | ✅ |
| 16 | Integration test | ✅ (42 tests passing) |
| 17 | Dev server + manual test | ✅ |
| — | Lucide React 圖示替換 | ✅ (額外) |
| — | Mock data 開發預覽 | ✅ (額外) |
| — | 分享卡 + Web Share API | ✅ (額外) |
| — | 手機 RWD 直式排版 | ✅ (額外) |
| — | Netlify + Render 部署 | ✅ (額外) |
| — | CI/CD 自動部署 | ✅ (額外) |
