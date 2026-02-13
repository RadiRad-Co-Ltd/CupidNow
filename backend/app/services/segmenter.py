"""Unified segmenter using jieba + dict.txt.big + 10K custom dict."""
import logging
import os
import re
import threading

import jieba

logger = logging.getLogger(__name__)
_initialized = False
_init_lock = threading.Lock()

_REPEAT_RE = re.compile(r"^(.)\1+$")
_NOISE_RE = re.compile(r"^[\s\d\W]+$")


def _is_trivial(text: str) -> bool:
    """Return True if text is unlikely to produce meaningful segmented words.

    Aggressive filter for chat messages:
    - ≤ 4 chars: almost always stop words / filler in Chinese chat
    - Repeated chars: "哈哈哈哈哈"
    - Pure noise: punctuation, digits, whitespace
    """
    if len(text) <= 4:
        return True
    if _REPEAT_RE.match(text):
        return True
    if _NOISE_RE.match(text):
        return True
    return False


def _ensure_initialized():
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        big_dict = os.path.join(data_dir, "dict.txt.big")
        if os.path.exists(big_dict):
            jieba.set_dictionary(big_dict)
            logger.info("jieba: loaded dict.txt.big")
        user_dict = os.path.join(data_dir, "user_dict.txt")
        if os.path.exists(user_dict):
            jieba.load_userdict(user_dict)
            logger.info("jieba: loaded user_dict.txt")
        jieba.initialize()
        _initialized = True
        logger.info("jieba initialized")


def cut(text: str) -> list[str]:
    """Segment a single string."""
    _ensure_initialized()
    return jieba.lcut(text)


def batch_cut(texts: list[str], progress: dict | None = None) -> list[list[str]]:
    """Batch segment with aggressive pre-filter + dedup.

    1. Pre-filter trivial texts (≤4 chars, noise, repeats) — skip entirely.
    2. Deduplicate remaining texts.
    3. Segment only unique non-trivial texts via jieba, then map results back.
    """
    if not texts:
        return []

    _ensure_initialized()

    # Build dedup map with pre-filter
    unique_map: dict[str, int] = {}
    unique_texts: list[str] = []
    text_indices: list[int] = []  # -1 = trivial (skipped)

    trivial_count = 0
    for t in texts:
        if _is_trivial(t):
            text_indices.append(-1)
            trivial_count += 1
            continue
        if t not in unique_map:
            unique_map[t] = len(unique_texts)
            unique_texts.append(t)
        text_indices.append(unique_map[t])

    logger.info(
        "batch_cut: %d total → %d trivial skipped → %d unique for jieba (%.0f%% saved)",
        len(texts), trivial_count, len(unique_texts),
        (1 - len(unique_texts) / max(len(texts), 1)) * 100,
    )

    # Segment unique texts
    unique_results = [jieba.lcut(t) for t in unique_texts]

    if progress is not None:
        progress["done"] = 1
        progress["total"] = 1

    # Map back to original order
    return [
        unique_results[idx] if idx >= 0 else [texts[i]]
        for i, idx in enumerate(text_indices)
    ]
