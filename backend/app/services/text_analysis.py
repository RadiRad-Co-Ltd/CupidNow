import re
from collections import Counter
from app.services.parser import Message
from app.services import segmenter

# Comprehensive Traditional Chinese stop words for chat analysis
STOP_WORDS = {
    # ── Pronouns ──
    "我", "你", "妳", "他", "她", "它", "我們", "你們", "他們", "她們",
    "自己", "大家", "人家", "別人", "某", "某個", "某些", "誰",
    # ── Demonstratives / interrogatives ──
    "這", "那", "這個", "那個", "這些", "那些", "這樣", "那樣",
    "這邊", "那邊", "這裡", "那裡", "這裏", "那裏",
    "什麼", "怎麼", "怎樣", "哪", "哪裡", "哪個", "哪些", "甚麼",
    # ── Structural particles ──
    "的", "了", "著", "過", "得", "地",
    # ── Common verbs / auxiliaries ──
    "是", "有", "在", "會", "要", "能", "可以", "可能",
    "去", "來", "到", "給", "讓", "把", "被", "跟", "說",
    "看", "想", "知道", "覺得", "感覺", "認為", "以為",
    "做", "弄", "搞", "用", "拿", "吃", "喝", "買", "走",
    # ── Adverbs ──
    "也", "都", "就", "才", "又", "再", "還", "很", "太", "好",
    "真", "超", "真的", "超級", "特別", "非常", "比較", "稍微",
    "已經", "正在", "一直", "一定", "應該", "大概", "可能",
    "其實", "當然", "不過", "反正", "幹嘛", "到底",
    "不", "沒", "沒有", "別", "不要", "不是", "不會", "不用",
    # ── Conjunctions / connectors ──
    "和", "跟", "與", "或", "但", "但是", "而", "而且", "所以",
    "因為", "如果", "雖然", "然後", "還是", "不然", "或者",
    "因此", "於是", "接著", "然而", "況且", "何況",
    # ── Prepositions / direction words ──
    "從", "向", "往", "對", "在", "到",
    "上", "下", "裡", "外", "前", "後", "中", "內",
    "上面", "下面", "裡面", "外面", "前面", "後面",
    "出來", "起來", "過來", "出去", "下去", "上去", "回來", "進去",
    # ── Measure words / numbers ──
    "一", "二", "三", "兩", "幾", "多", "少",
    "一個", "一些", "一下", "一點", "一樣", "一起", "一直",
    # ── Time words ──
    "今天", "明天", "昨天", "現在", "剛才", "等等", "之後", "之前",
    "時候", "早上", "下午", "晚上", "中午", "待會", "剛剛", "馬上",
    # ── Sentence-final particles / interjections ──
    "嗎", "呢", "吧", "啊", "喔", "哦", "欸", "耶", "喂", "唉",
    "嘿", "嗯", "恩", "呀", "哈", "嘻", "哇", "噢", "嗚", "齁",
    "啦", "囉", "喲", "呦", "蛤", "咦", "誒", "唷", "捏", "膩",
    "嘛", "咧", "哩", "吶", "哎", "噓", "嘖", "唄", "咳", "呃",
    "哎呀", "哎喲", "嗯嗯", "欸欸", "喔喔", "嗚嗚", "哇哇",
    # ── Chat fillers / responses ──
    "好", "對", "沒",
    "好啊", "好喔", "好哦", "好啦", "好吧", "好的", "好嗎", "好呀", "好ㄛ",
    "對啊", "對呀", "對喔", "對吧", "對對", "對對對",
    "是啊", "是喔", "是嗎", "是呀", "是吧",
    "哈哈", "哈哈哈", "哈哈哈哈", "嘿嘿", "嘻嘻", "呵呵", "嘎嘎",
    "謝謝", "謝", "感謝", "拜拜", "掰掰", "掰",
    "OK", "ok", "Ok", "嗯嗯嗯", "恩恩",
    "知道了", "了解", "收到", "明白", "沒事", "沒關係", "不客氣",
    "隨便", "都可以", "無所謂", "看你", "都行",
    # ── Greetings / farewells ──
    "嗨", "哈囉", "你好", "安安", "早安", "午安", "晚安",
    "嗨嗨", "哈囉哈囉",
    # ── Filler / linking phrases ──
    "就是", "好像", "似乎", "差不多", "原來", "難怪", "總之",
    "結果", "忽然", "突然", "終於", "果然", "居然", "竟然",
    "而已", "罷了", "這麼", "那麼", "多少", "起碼", "至少",
    "不過是", "無論", "不管", "只是", "只要", "只有",
    # ── Negation patterns ──
    "不能", "不行", "不可以", "不知道", "不想", "不好", "不對",
    "沒辦法", "不確定", "不一定", "不太", "不夠",
    # ── Common single-char verbs (high freq, low info) ──
    "聽", "講", "問", "答", "找", "放", "帶", "送", "開", "關",
    "坐", "站", "睡", "穿", "寫", "讀", "玩", "打", "叫", "等",
    "回", "起", "先", "算", "學", "教", "選", "換", "留", "猜",
    # ── Duplicated casual verbs ──
    "看看", "想想", "試試", "說說", "聊聊", "等等", "走走",
    # ── Common adjectives / descriptors (generic) ──
    "快", "慢", "大", "小", "長", "短", "高", "低", "早", "晚",
    "新", "舊", "全", "每", "整", "各",
    # ── Quantifiers / scope words ──
    "全部", "所有", "每個", "整個", "任何", "其他", "另外",
    # ── Time expressions (extended) ──
    "最近", "以前", "以後", "將來", "永遠", "經常", "常常",
    "通常", "有時", "有時候", "偶爾", "最後", "首先",
    "那時", "那時候", "這時", "這時候", "同時", "隨時",
    "今年", "明年", "去年", "這週", "下週", "上週",
    # ── Measure words ──
    "個", "隻", "件", "次", "天", "年", "月", "分", "秒",
    "塊", "杯", "碗", "盤", "瓶", "包", "張", "本",
    # ── Chat emoticon text ──
    "XD", "xd", "QQ", "qq", "XDD", "xdd", "XDDD", "xddd",
    # ── Generic nouns ──
    "東西", "地方", "事情", "樣子", "意思", "問題", "方面",
    "部分", "情況", "感覺", "機會", "關係",
    "時間", "方式", "辦法", "原因", "結果", "目的",
    "自己", "對方", "彼此",
    # ── LINE system text ──
    "收回", "訊息", "已讀", "貼圖", "圖片", "影片", "檔案",
    "通話", "語音", "相簿", "記事本", "傳送",
    # ── URL fragments ──
    "http", "https", "www", "com", "tw", "org", "net", "io",
    "html", "php", "aspx", "htm",
}

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# ── Shared interest category keywords ──
# Suffixes / patterns that hint at a category
_PLACE_HINTS = {
    "區", "路", "街", "站", "山", "湖", "海", "灣", "島", "港", "園",
    "寺", "廟", "堂", "館", "場", "城", "鎮", "村", "里", "巷",
    "夜市", "老街", "商圈", "百貨", "公園", "車站", "機場", "碼頭",
}
_FOOD_HINTS = {
    "麵", "飯", "湯", "粥", "鍋", "餅", "包", "糕", "酥", "捲",
    "雞", "豬", "牛", "魚", "蝦", "蛋", "肉", "菜", "豆", "奶",
    "茶", "咖啡", "珍奶", "奶茶", "拿鐵", "啤酒", "紅酒",
    "拉麵", "火鍋", "壽司", "披薩", "漢堡", "炸雞", "滷味",
    "甜點", "蛋糕", "冰淇淋", "布丁", "鬆餅", "巧克力",
    "餐廳", "小吃", "早餐", "午餐", "晚餐", "宵夜", "便當",
}
_SHOW_HINTS = {
    "電影", "影集", "韓劇", "日劇", "陸劇", "台劇", "美劇",
    "動漫", "動畫", "漫畫", "Netflix", "netflix", "Disney",
    "綜藝", "節目", "紀錄片", "影片", "預告",
}
_MUSIC_HINTS = {
    "歌", "曲", "專輯", "演唱會", "音樂", "樂團", "歌手",
    "Spotify", "spotify", "KKBOX", "kkbox", "YouTube", "youtube",
    "MV", "mv", "播放", "旋律",
}
_ACTIVITY_HINTS = {
    "逛街", "看電影", "散步", "跑步", "健身", "游泳", "爬山",
    "旅行", "出國", "露營", "野餐", "唱歌", "KTV", "桌遊",
    "遊戲", "打球", "瑜珈", "騎車", "開車", "搭車",
    "購物", "買東西", "約會", "聚餐", "慶祝",
}

_CATEGORIES = [
    ("愛去的地方", _PLACE_HINTS),
    ("愛吃的東西", _FOOD_HINTS),
    ("愛看的劇", _SHOW_HINTS),
    ("愛聽的音樂", _MUSIC_HINTS),
    ("常一起做的事", _ACTIVITY_HINTS),
]


def _categorize_word(word: str) -> str | None:
    """Return category name if word matches any hint, else None."""
    for category, hints in _CATEGORIES:
        if word in hints:
            return category
        for hint in hints:
            if len(hint) >= 2 and hint in word:
                return category
            if len(word) >= 2 and word.endswith(hint) and len(hint) == 1:
                return category
    return None


def _extract_shared_interests(
    all_words_by_person: dict[str, Counter], persons: list[str]
) -> list[dict]:
    """Extract shared interests from word frequency data."""
    if len(persons) < 2:
        return []

    p1, p2 = persons[0], persons[1]
    # Merge both persons' word counts
    combined = Counter()
    for w in set(all_words_by_person[p1]) | set(all_words_by_person[p2]):
        combined[w] = all_words_by_person[p1].get(w, 0) + all_words_by_person[p2].get(w, 0)

    # Categorize words
    categorized: dict[str, list[tuple[str, int]]] = {}
    for word, count in combined.most_common(500):
        cat = _categorize_word(word)
        if cat:
            if cat not in categorized:
                categorized[cat] = []
            if len(categorized[cat]) < 5:
                categorized[cat].append((word, count))

    # Build result in fixed category order
    result = []
    for cat_name, _ in _CATEGORIES:
        items = categorized.get(cat_name, [])
        if items:
            result.append({
                "category": cat_name,
                "items": [{"name": w, "count": c} for w, c in items],
            })

    return result


def merge_shared_interests(
    jieba_interests: list[dict], ai_interests: list | None
) -> list[dict]:
    """Merge jieba keyword-based and AI-extracted shared interests.

    jieba provides {category, items: [{name, count}]} with frequency counts.
    AI provides {category, items: [str]} with richer context but no counts.
    Result: deduplicated, jieba items first (with counts), AI-only items appended.
    """
    if not ai_interests:
        return jieba_interests

    # Index jieba results by category
    merged: dict[str, dict[str, int | None]] = {}
    category_order: list[str] = []

    for entry in jieba_interests:
        cat = entry["category"]
        if cat not in merged:
            merged[cat] = {}
            category_order.append(cat)
        for item in entry.get("items", []):
            if isinstance(item, dict):
                merged[cat][item["name"]] = item.get("count")
            else:
                merged[cat][str(item)] = None

    # Merge AI results
    for entry in ai_interests:
        cat = entry.get("category", "")
        if not cat:
            continue
        if cat not in merged:
            merged[cat] = {}
            category_order.append(cat)
        for item in entry.get("items", []):
            name = item["name"] if isinstance(item, dict) else str(item)
            if name not in merged[cat]:
                merged[cat][name] = item.get("count") if isinstance(item, dict) else None

    # Build final list, cap 8 items per category
    result = []
    for cat in category_order:
        items = merged[cat]
        if not items:
            continue
        sorted_items = sorted(
            items.items(),
            key=lambda x: (x[1] is not None, x[1] or 0),
            reverse=True,
        )
        result.append({
            "category": cat,
            "items": [
                {"name": n, "count": c} if c is not None else {"name": n}
                for n, c in sorted_items[:8]
            ],
        })

    return result


def compute_text_analysis(parsed: dict) -> dict:
    messages: list[Message] = parsed["messages"]
    persons: list[str] = parsed["persons"]

    # 收集每人的文字訊息
    texts_by_person: dict[str, list[str]] = {p: [] for p in persons}
    for m in messages:
        if m.msg_type == "text":
            texts_by_person[m.sender].append(_URL_RE.sub("", m.content))

    # 批次分詞（CKIP or jieba fallback）
    all_texts: list[str] = []
    person_ranges: list[tuple[str, int, int]] = []  # (person, start, end)
    for p in persons:
        start = len(all_texts)
        all_texts.extend(texts_by_person[p])
        person_ranges.append((p, start, len(all_texts)))

    all_words = segmenter.batch_cut(all_texts)

    # 統計
    word_cloud = {}
    all_words_by_person: dict[str, Counter] = {}

    for person, start, end in person_ranges:
        counter: Counter = Counter()
        for word_list in all_words[start:end]:
            filtered = [
                w for w in word_list
                if len(w) >= 2
                and w not in STOP_WORDS
                and not re.match(r"^[\d\W]+$", w)
                and not re.match(r"^(.)\1+$", w)
            ]
            counter.update(filtered)
        all_words_by_person[person] = counter
        word_cloud[person] = [
            {"word": w, "count": c}
            for w, c in counter.most_common(80)
        ]

    # Unique phrases: words that appear disproportionately in THIS chat
    # Simple approach: words used by both persons (shared vocabulary)
    if len(persons) == 2:
        p1, p2 = persons
        shared = set(all_words_by_person[p1]) & set(all_words_by_person[p2])
        unique = sorted(
            shared,
            key=lambda w: all_words_by_person[p1][w] + all_words_by_person[p2][w],
            reverse=True,
        )[:20]
        unique_phrases = [
            {
                "phrase": w,
                "count": all_words_by_person[p1][w] + all_words_by_person[p2][w],
            }
            for w in unique
        ]
    else:
        unique_phrases = []

    shared_interests = _extract_shared_interests(all_words_by_person, persons)

    return {
        "wordCloud": word_cloud,
        "uniquePhrases": unique_phrases,
        "sharedInterests": shared_interests,
    }
