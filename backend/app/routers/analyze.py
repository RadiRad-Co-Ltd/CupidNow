import logging
import time
from collections import defaultdict

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.services.cold_war import detect_cold_wars
from app.services.parser import parse_line_chat
from app.services.reply_analysis import compute_reply_behavior
from app.services.stats import compute_basic_stats
from app.services.text_analysis import compute_text_analysis
from app.services.time_patterns import compute_time_patterns

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

_rate_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 10
RATE_WINDOW = 60


def _check_rate_limit(ip: str) -> None:
    now = time.time()
    window_start = now - RATE_WINDOW
    _rate_store[ip] = [t for t in _rate_store[ip] if t > window_start]
    if len(_rate_store[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests")
    _rate_store[ip].append(now)

    if len(_rate_store) > 1000:
        stale = [k for k, v in _rate_store.items() if not v or v[-1] < window_start]
        for k in stale:
            del _rate_store[k]


@router.post("/analyze")
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    skip_ai: bool = Form(default=False),
):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    raw_data = await file.read()
    if len(raw_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    try:
        text = raw_data.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding")
    finally:
        raw_data = b""

    parsed = parse_line_chat(text)
    text = ""

    if not parsed["messages"]:
        raise HTTPException(status_code=400, detail="No messages found in file")

    persons = parsed["persons"]

    basic_stats = compute_basic_stats(parsed)
    reply_behavior = compute_reply_behavior(parsed)
    time_patterns = compute_time_patterns(parsed)
    cold_wars = detect_cold_wars(parsed)
    text_analysis = compute_text_analysis(parsed)

    ai_result = None
    if not skip_ai:
        try:
            from app.services.ai_analysis import analyze_with_ai
            ai_result = await analyze_with_ai(parsed["messages"], persons)
        except Exception:
            logger.exception("AI analysis failed")
            ai_result = None

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
