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
