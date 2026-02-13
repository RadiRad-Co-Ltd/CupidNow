"""Unified segmenter using CKIP albert-tiny (singleton, kept in memory)."""
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
    """Batch segment using CKIP. Processes in chunks to limit per-batch memory."""
    if not texts:
        return []

    ws = _get_ws()
    all_results: list[list[str]] = []
    chunk_size = 256
    for i in range(0, len(texts), chunk_size):
        chunk = texts[i : i + chunk_size]
        results = ws(chunk, batch_size=256, max_length=128)
        all_results.extend(list(sent) for sent in results)
    return all_results
