import asyncio
import gc
import json
import logging
import time
from collections import defaultdict
from typing import AsyncGenerator

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from app.services.cold_war import detect_cold_wars
from app.services.first_conversation import extract_first_conversation
from app.services.parser import parse_line_chat
from app.services.reply_analysis import compute_reply_behavior
from app.services.stats import compute_basic_stats
from app.services.text_analysis import compute_text_analysis
from app.services.time_patterns import compute_time_patterns
from app.services.transfer_analysis import compute_transfer_analysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

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


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


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
        raise HTTPException(status_code=413, detail="File too large (max 20MB)")

    try:
        text = raw_data.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding")
    finally:
        raw_data = b""

    parsed = parse_line_chat(text)
    del text

    if not parsed["messages"]:
        raise HTTPException(status_code=400, detail="No messages found in file")

    persons = parsed["persons"]

    basic_stats = compute_basic_stats(parsed)
    reply_behavior = compute_reply_behavior(parsed)
    time_patterns = compute_time_patterns(parsed)
    cold_wars = detect_cold_wars(parsed)
    text_analysis, interest_context = compute_text_analysis(parsed)
    transfer_analysis = compute_transfer_analysis(parsed)
    first_conversation = extract_first_conversation(parsed)

    # Extract internal data for AI sampling, then clean up
    word_idf = text_analysis.pop("_word_idf", None)
    msg_words = text_analysis.pop("_msg_words", None)

    ai_result = None
    if not skip_ai:
        try:
            from app.services.ai_analysis import analyze_with_ai
            ai_stats = {
                "basicStats": basic_stats,
                "replyBehavior": reply_behavior,
                "coldWars": cold_wars,
                "textAnalysis": text_analysis,
            }
            ai_result = await analyze_with_ai(
                parsed["messages"], persons, ai_stats,
                interest_context=interest_context,
                msg_words=msg_words, word_idf=word_idf,
            )
        except Exception:
            logger.exception("AI analysis failed")
            ai_result = None

    del parsed, word_idf, msg_words
    gc.collect()

    # AI sharedInterests priority + jieba category backfill
    if ai_result:
        ai_si = ai_result.pop("sharedInterests", None)
        if ai_si:
            ai_cats = {e["category"] for e in ai_si}
            for entry in text_analysis.get("sharedInterests", []):
                if entry["category"] not in ai_cats:
                    ai_si.append(entry)
            text_analysis["sharedInterests"] = ai_si
        # else: keep jieba sharedInterests as fallback

    result = {
        "persons": persons,
        "basicStats": basic_stats,
        "replyBehavior": reply_behavior,
        "timePatterns": time_patterns,
        "coldWars": cold_wars,
        "textAnalysis": text_analysis,
    }

    if transfer_analysis:
        result["transferAnalysis"] = transfer_analysis

    if first_conversation:
        result["firstConversation"] = first_conversation

    if ai_result:
        result["aiAnalysis"] = ai_result

    return result


@router.post("/analyze-stream")
async def analyze_stream(
    request: Request,
    file: UploadFile = File(...),
    skip_ai: bool = Form(default=False),
):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    raw_data = await file.read()
    if len(raw_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 20MB)")

    try:
        text = raw_data.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding")
    finally:
        raw_data = b""

    async def event_stream() -> AsyncGenerator[str, None]:
        yield _sse_event({"progress": 5, "stage": "解析對話記錄中..."})
        await asyncio.sleep(0)

        parsed = parse_line_chat(text)
        if not parsed["messages"]:
            yield _sse_event({"error": "找不到任何訊息"})
            return

        total = len(parsed["messages"])
        persons = parsed["persons"]
        yield _sse_event({"progress": 15, "stage": f"已解析 {total:,} 則訊息，計算基礎統計..."})
        await asyncio.sleep(0)

        basic_stats = compute_basic_stats(parsed)
        yield _sse_event({"progress": 30, "stage": "分析回覆行為..."})
        await asyncio.sleep(0)

        reply_behavior = compute_reply_behavior(parsed)
        yield _sse_event({"progress": 45, "stage": "分析時間模式..."})
        await asyncio.sleep(0)

        time_patterns = compute_time_patterns(parsed)
        yield _sse_event({"progress": 55, "stage": "偵測冷戰期間..."})
        await asyncio.sleep(0)

        cold_wars = detect_cold_wars(parsed)
        yield _sse_event({"progress": 65, "stage": "分析文字內容與文字雲..."})
        await asyncio.sleep(0)

        # Run jieba segmentation in a thread to avoid blocking event loop
        text_analysis, interest_context = await asyncio.get_running_loop().run_in_executor(
            None, compute_text_analysis, parsed
        )

        # Extract internal data for AI sampling, then clean up
        word_idf = text_analysis.pop("_word_idf", None)
        msg_words = text_analysis.pop("_msg_words", None)

        transfer_analysis = compute_transfer_analysis(parsed)
        first_conversation = extract_first_conversation(parsed)

        result = {
            "persons": persons,
            "basicStats": basic_stats,
            "replyBehavior": reply_behavior,
            "timePatterns": time_patterns,
            "coldWars": cold_wars,
            "textAnalysis": text_analysis,
        }

        if transfer_analysis:
            result["transferAnalysis"] = transfer_analysis

        if first_conversation:
            result["firstConversation"] = first_conversation

        ai_result = None
        ai_warning = None
        if not skip_ai:
            yield _sse_event({"progress": 75, "stage": "AI 正在解讀你們的故事..."})
            await asyncio.sleep(0)
            try:
                from app.services.ai_analysis import analyze_with_ai, AIRateLimitError
                ai_stats = {
                    "basicStats": basic_stats,
                    "replyBehavior": reply_behavior,
                    "coldWars": cold_wars,
                    "textAnalysis": text_analysis,
                }
                messages = parsed["messages"]
                ai_result = await analyze_with_ai(
                    messages, persons, ai_stats,
                    interest_context=interest_context,
                    msg_words=msg_words, word_idf=word_idf,
                )
                del messages
            except AIRateLimitError:
                logger.warning("AI rate limited, skipping AI analysis")
                ai_warning = "AI 分析額度已達今日上限，其他數據分析仍然完整！請稍後再試即可補上 AI 洞察。"
            except Exception:
                logger.exception("AI analysis failed")
                ai_result = None

        # Release parsed messages from memory
        del parsed, word_idf, msg_words
        gc.collect()

        # AI sharedInterests priority + jieba category backfill
        if ai_result:
            ai_si = ai_result.pop("sharedInterests", None)
            if ai_si:
                ai_cats = {e["category"] for e in ai_si}
                for entry in result["textAnalysis"].get("sharedInterests", []):
                    if entry["category"] not in ai_cats:
                        ai_si.append(entry)
                result["textAnalysis"]["sharedInterests"] = ai_si
            # else: keep jieba sharedInterests as fallback
            result["aiAnalysis"] = ai_result

        final_event: dict = {"progress": 100, "stage": "完成！", "result": result}
        if ai_warning:
            final_event["warning"] = ai_warning
        yield _sse_event(final_event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
