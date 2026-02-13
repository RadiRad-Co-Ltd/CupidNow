"""Unified segmenter: CKIP (primary) → jieba (fallback)."""
import gc
import logging
import os
from pathlib import Path

import jieba

logger = logging.getLogger(__name__)

# ── jieba fallback 初始化 ──
_jieba_ready = False


def _init_jieba():
    global _jieba_ready
    if _jieba_ready:
        return
    _jieba_ready = True
    # 繁中大辭典
    dict_big = os.path.join(os.path.dirname(jieba.__file__), "dict.txt.big")
    if os.path.exists(dict_big):
        jieba.set_dictionary(dict_big)
    # 自訂辭典
    user_dict = Path(__file__).resolve().parent.parent.parent / "data" / "user_dict.txt"
    if user_dict.exists():
        jieba.load_userdict(str(user_dict))
    jieba.initialize()


def cut(text: str) -> list[str]:
    """Segment a single string. Used for lightweight per-message checks."""
    _init_jieba()
    return jieba.lcut(text)


def batch_cut(texts: list[str]) -> list[list[str]]:
    """Batch segment using CKIP, fallback to jieba if unavailable.

    Loads CKIP model on demand, processes all texts, then unloads.
    """
    if not texts:
        return []

    # Try CKIP
    try:
        return _ckip_batch(texts)
    except Exception:
        logger.warning("CKIP unavailable, falling back to jieba", exc_info=True)

    # Fallback: jieba
    _init_jieba()
    return [jieba.lcut(t) for t in texts]


def _ckip_batch(texts: list[str]) -> list[list[str]]:
    """Load CKIP, segment, unload."""
    from ckip_transformers.nlp import CkipWordSegmenter

    ws = CkipWordSegmenter(model="albert-tiny", device=-1)
    try:
        results = ws(texts, batch_size=64, max_length=128)
        return [list(sent) for sent in results]
    finally:
        del ws
        gc.collect()
