"""Unified segmenter using CKIP albert-tiny (singleton, kept in memory).

Optimization: dedup texts before inference, skip trivially short messages.
"""
import logging

logger = logging.getLogger(__name__)

_ws = None


def _get_ws():
    """Lazy-load CKIP word segmenter once, keep in memory."""
    global _ws
    if _ws is None:
        from ckip_transformers.nlp import CkipWordSegmenter
        logger.info("Loading CKIP albert-tiny model...")
        _ws = CkipWordSegmenter(model="albert-tiny", device=-1)
        logger.info("CKIP model loaded")
    return _ws


def cut(text: str) -> list[str]:
    """Segment a single string."""
    ws = _get_ws()
    results = ws([text], batch_size=1, max_length=128)
    return list(results[0])


def batch_cut(texts: list[str]) -> list[list[str]]:
    """Batch segment using CKIP with dedup optimization.

    1. Skip trivially short texts (≤1 char) — they can't produce useful words.
    2. Deduplicate — chat logs have massive repetition.
    3. Segment only unique texts, then map results back.
    """
    if not texts:
        return []

    # Build dedup map: unique text → index in unique list
    unique_map: dict[str, int] = {}
    unique_texts: list[str] = []
    text_indices: list[int] = []  # maps original index → unique index (-1 = skipped)

    for t in texts:
        if len(t) <= 1:
            text_indices.append(-1)
            continue
        if t not in unique_map:
            unique_map[t] = len(unique_texts)
            unique_texts.append(t)
        text_indices.append(unique_map[t])

    logger.info(
        "batch_cut: %d total → %d unique (%.0f%% dedup)",
        len(texts), len(unique_texts),
        (1 - len(unique_texts) / max(len(texts), 1)) * 100,
    )

    # Segment unique texts only
    if unique_texts:
        ws = _get_ws()
        unique_results: list[list[str]] = []
        chunk_size = 256
        for i in range(0, len(unique_texts), chunk_size):
            chunk = unique_texts[i : i + chunk_size]
            results = ws(chunk, batch_size=256, max_length=128)
            unique_results.extend(list(sent) for sent in results)
    else:
        unique_results = []

    # Map back to original order
    return [
        unique_results[idx] if idx >= 0 else [texts[i]]
        for i, idx in enumerate(text_indices)
    ]
