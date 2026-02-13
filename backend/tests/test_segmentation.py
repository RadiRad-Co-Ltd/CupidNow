from app.services.segmenter import cut, batch_cut


class TestCut:
    """cut() uses jieba — verify custom dict works."""

    def test_place_name(self):
        assert "信義區" in cut("我們去信義區逛街")

    def test_food(self):
        assert "珍奶" in cut("下午來喝珍奶")

    def test_night_market(self):
        assert "師大夜市" in cut("去師大夜市吃東西")


class TestBatchCut:
    """batch_cut() uses CKIP (or fallback to jieba)."""

    def test_returns_list_of_lists(self):
        results = batch_cut(["你好嗎", "今天天氣好"])
        assert len(results) == 2
        assert all(isinstance(r, list) for r in results)

    def test_empty_input(self):
        assert batch_cut([]) == []

    def test_traditional_chinese_quality(self):
        results = batch_cut(["我們明天去信義區吃拉麵好不好"])
        words = results[0]
        # CKIP or jieba should keep these as single tokens
        assert "信義區" in words
        assert "拉麵" in words

    def test_sticker_label_passthrough(self):
        """Non-text content should still be segmentable."""
        results = batch_cut(["哈哈好好笑"])
        assert len(results) == 1
        assert len(results[0]) > 0
