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
