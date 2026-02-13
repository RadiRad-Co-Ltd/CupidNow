from app.services.segmenter import cut, batch_cut


class TestCut:
    """cut() uses CKIP for single text segmentation."""

    def test_place_name(self):
        assert "信義區" in cut("我們去信義區逛街")

    def test_food(self):
        words = cut("下午來喝珍珠奶茶")
        assert "珍珠奶茶" in words or "珍珠" in words

    def test_returns_list(self):
        result = cut("你好嗎")
        assert isinstance(result, list)
        assert len(result) > 0


class TestBatchCut:
    """batch_cut() uses CKIP for batch segmentation."""

    def test_returns_list_of_lists(self):
        results = batch_cut(["你好嗎", "今天天氣好"])
        assert len(results) == 2
        assert all(isinstance(r, list) for r in results)

    def test_empty_input(self):
        assert batch_cut([]) == []

    def test_traditional_chinese_quality(self):
        results = batch_cut(["我們明天去信義區吃拉麵好不好"])
        words = results[0]
        assert "信義區" in words
        assert "拉麵" in words

    def test_sticker_label_passthrough(self):
        results = batch_cut(["哈哈好好笑"])
        assert len(results) == 1
        assert len(results[0]) > 0

    def test_large_batch(self):
        """Verify chunking works for batches > chunk_size."""
        texts = ["今天天氣好"] * 300
        results = batch_cut(texts)
        assert len(results) == 300
