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

# ── Shared interest: explicit word-to-category lookup ──
# Built from user_dict.txt categories. Only exact matches — no suffix guessing.
import os as _os
import logging as _logging

_interest_logger = _logging.getLogger(__name__)

_CATEGORY_ORDER = ["愛去的地方", "愛吃的東西", "愛看的劇", "愛聽的音樂", "常一起做的事"]

# Explicit word sets — no single-char suffix matching
_PLACE_WORDS: set[str] = set()
_FOOD_WORDS: set[str] = set()
_SHOW_WORDS: set[str] = set()
_MUSIC_WORDS: set[str] = set()
_ACTIVITY_WORDS: set[str] = set()

# Generic words to exclude even if they match a category
_BORING_WORDS = {
    # 日常動作
    "吃飯", "逛街", "買東西", "回家", "出門", "出去", "上班", "下班",
    "上課", "下課", "睡覺", "起床", "走路", "開車", "騎車", "搭車",
    "聊天", "拍照", "購物", "打電話", "傳訊息", "看影片",
    "早餐", "午餐", "晚餐", "白飯", "喝水",
    # Generic 分類詞（不是具體興趣）
    "韓劇", "日劇", "陸劇", "台劇", "美劇", "追劇", "看劇",
    "電影", "看電影", "動漫", "動畫", "漫畫", "綜藝", "紀錄片",
    "唱歌", "音樂", "聽歌", "聽音樂", "歌手", "樂團",
    "散步", "跑步", "運動", "旅行", "旅遊", "出國",
    "約會", "聚餐", "健身", "游泳", "騎車", "騎腳踏車",
    "料理", "下廚", "煮飯", "烘焙",
    "遊戲", "玩遊戲", "打電動", "手遊",
}

_word_to_category: dict[str, str] = {}
_interest_loaded = False


def _load_interest_words():
    """Build word→category lookup from user_dict.txt and hardcoded sets."""
    global _interest_loaded
    if _interest_loaded:
        return
    _interest_loaded = True

    # Hardcoded high-value words per category (always available even without user_dict)
    _PLACE_WORDS.update({
        # 夜市
        "士林夜市", "饒河夜市", "寧夏夜市", "通化夜市", "逢甲夜市",
        "六合夜市", "瑞豐夜市", "師大夜市", "公館夜市", "花園夜市",
        "羅東夜市", "基隆廟口", "樂華夜市", "南機場夜市",
        # 景點
        "台北101", "陽明山", "象山步道", "貓空纜車", "九份老街",
        "十分老街", "淡水老街", "西門町", "永康街", "迪化街",
        "華山文創", "松菸文創", "日月潭", "阿里山", "太魯閣",
        "清境農場", "合歡山", "墾丁", "綠島", "蘭嶼", "小琉球",
        "澎湖", "金門", "馬祖", "高美濕地", "彩虹眷村",
        "駁二藝術特區", "奇美博物館", "赤崁樓", "安平古堡",
        "北投溫泉", "烏來溫泉", "礁溪溫泉", "知本溫泉",
        "七星潭", "伯朗大道", "三仙台", "鵝鑾鼻燈塔",
        "忘憂森林", "溪頭", "杉林溪", "宮原眼科", "審計新村",
        # 行政區
        "信義區", "大安區", "中山區", "松山區", "內湖區", "士林區",
        "北投區", "中正區", "萬華區", "文山區", "南港區",
        "板橋區", "新莊區", "三重區", "永和區", "中和區",
        "新店區", "淡水區", "汐止區", "土城區", "蘆洲區", "林口區",
        "桃園區", "中壢區", "竹北市",
        # 商圈/百貨
        "信義商圈", "東區商圈", "西門商圈", "逢甲商圈", "一中商圈",
        "新光三越", "微風廣場", "誠品書店",
        # 捷運站
        "台北車站", "忠孝復興", "忠孝敦化", "市政府站", "西門站",
        "板橋站", "美麗島站",
    })

    _FOOD_WORDS.update({
        "珍珠奶茶", "珍奶", "鹹酥雞", "雞排", "滷味", "牛肉麵",
        "小籠包", "臭豆腐", "蚵仔煎", "大腸包小腸", "胡椒餅",
        "車輪餅", "豬血糕", "蚵仔麵線", "魯肉飯", "滷肉飯",
        "鳳梨酥", "太陽餅", "芋圓", "豆花", "芒果冰", "愛玉",
        "麻辣鍋", "薑母鴨", "羊肉爐", "麻辣燙", "蛋餅",
        "拉麵", "壽司", "生魚片", "義大利麵", "披薩", "漢堡",
        "鬆餅", "可頌", "提拉米蘇", "舒芙蕾", "千層蛋糕",
        "冰淇淋", "拿鐵", "卡布奇諾", "美式咖啡", "手沖咖啡",
        "抹茶拿鐵", "黑糖鮮奶", "波霸奶茶", "黑糖波霸",
        "火鍋", "涮涮鍋", "石頭鍋", "麻辣火鍋", "海鮮鍋",
        "韓式炸雞", "韓式烤肉", "壽喜燒", "燒肉",
        "咖哩飯", "炸雞排", "鍋貼", "水餃", "蔥油餅",
        "調酒", "啤酒", "紅酒", "威士忌", "精釀啤酒",
        "下午茶", "宵夜", "早午餐", "吃到飽", "Buffet", "brunch",
        "鼎泰豐", "海底撈", "築間", "馬辣", "爭鮮", "壽司郎",
        "星巴克", "路易莎", "五十嵐", "迷客夏", "可不可",
        "春水堂", "老虎堂", "大苑子", "清心福全",
    })

    _SHOW_WORDS.update({
        "電影", "影集", "韓劇", "日劇", "陸劇", "台劇", "美劇",
        "動漫", "動畫", "漫畫", "Netflix", "Disney+",
        "綜藝", "紀錄片", "追劇", "看劇", "看電影",
        "YouTube", "愛奇藝",
    })

    _MUSIC_WORDS.update({
        "演唱會", "音樂", "樂團", "歌手", "音樂祭", "音樂節",
        "Spotify", "KKBOX", "Apple Music",
        "彈吉他", "彈鋼琴", "打鼓", "彈烏克麗麗",
        "聽音樂", "聽歌", "唱歌", "唱KTV", "KTV", "K歌",
    })

    _ACTIVITY_WORDS.update({
        "健身", "重訓", "瑜珈", "游泳", "跑步", "慢跑", "路跑",
        "爬山", "登山", "健行", "露營", "野餐", "釣魚",
        "衝浪", "潛水", "浮潛", "滑雪", "攀岩", "溯溪",
        "打籃球", "打棒球", "打排球", "打羽球", "打桌球",
        "打網球", "踢足球", "打保齡球",
        "桌遊", "密室逃脫", "夾娃娃", "打電動", "玩遊戲",
        "看展覽", "看表演", "看舞台劇", "泡溫泉", "做SPA",
        "烘焙", "料理", "下廚", "手作",
        "攝影", "畫畫", "閱讀", "寫日記",
        "旅行", "旅遊", "出國", "自由行", "環島",
        "約會", "聚餐", "散步", "騎腳踏車",
        "遊樂園", "六福村", "劍湖山", "動物園", "水族館",
    })

    # Build word→category lookup
    for w in _PLACE_WORDS:
        _word_to_category[w] = "愛去的地方"
    for w in _FOOD_WORDS:
        _word_to_category[w] = "愛吃的東西"
    for w in _SHOW_WORDS:
        _word_to_category[w] = "愛看的劇"
    for w in _MUSIC_WORDS:
        _word_to_category[w] = "愛聽的音樂"
    for w in _ACTIVITY_WORDS:
        _word_to_category[w] = "常一起做的事"

    # Also load from user_dict.txt — words with pos 'ns' → place, 'n' with food keywords → food
    data_dir = _os.path.join(_os.path.dirname(__file__), "..", "..", "data")
    user_dict = _os.path.join(data_dir, "user_dict.txt")
    if _os.path.exists(user_dict):
        added = 0
        with open(user_dict, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    word, _, pos = parts[0], parts[1], parts[2]
                    if len(word) >= 2 and word not in _word_to_category:
                        if pos == "ns":
                            _word_to_category[word] = "愛去的地方"
                            added += 1
                        elif pos == "nz":
                            # brands — skip, not an interest category
                            pass
        _interest_logger.info("interest lookup: %d from hardcoded + %d from user_dict", len(_word_to_category) - added, added)


def _tfidf_score(word: str, tf: int, total_msgs: int) -> float:
    """TF-IDF score using jieba's built-in word frequency as corpus proxy.

    High score = word is frequent in THIS chat but rare in general Chinese.
    This naturally suppresses generic words like 吃飯/逛街 (high corpus freq)
    and promotes distinctive words like 珍珠奶茶/密室逃脫 (low corpus freq).
    """
    import math
    import jieba

    # TF: normalize by total message count
    tf_norm = tf / max(total_msgs, 1)

    # IDF: use jieba's corpus frequency as a proxy
    # jieba.dt.FREQ stores {word: freq_count}, total is jieba.dt.total
    corpus_freq = jieba.dt.FREQ.get(word, 0)
    corpus_total = jieba.dt.total or 1
    # Smoothed IDF — words not in jieba dict get highest IDF
    if corpus_freq > 0:
        idf = math.log((corpus_total + 1) / (corpus_freq + 1))
    else:
        # Not in jieba dict at all — very distinctive (custom dict / rare word)
        idf = math.log(corpus_total + 1)

    return tf_norm * idf


def _extract_shared_interests(
    all_words_by_person: dict[str, Counter], persons: list[str],
    total_msgs: int = 0,
) -> list[dict]:
    """Extract shared interests using TF-IDF scoring.

    1. Only words BOTH people mention (truly shared).
    2. Categorize by explicit word→category lookup (no suffix guessing).
    3. Rank by TF-IDF: frequent in this chat but rare in general Chinese.
    """
    if len(persons) < 2:
        return []

    _load_interest_words()

    p1, p2 = persons[0], persons[1]
    shared_words = set(all_words_by_person[p1]) & set(all_words_by_person[p2])

    categorized: dict[str, list[tuple[str, int, float]]] = {}
    for w in shared_words:
        if w in _BORING_WORDS or len(w) < 2:
            continue
        cat = _word_to_category.get(w)
        if not cat:
            continue
        total = all_words_by_person[p1][w] + all_words_by_person[p2][w]
        score = _tfidf_score(w, total, total_msgs)
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append((w, total, score))

    # Sort by TF-IDF score (not raw count), take top 6
    result = []
    for cat_name in _CATEGORY_ORDER:
        items = categorized.get(cat_name, [])
        if items:
            items.sort(key=lambda x: x[2], reverse=True)
            result.append({
                "category": cat_name,
                "items": [{"name": w, "count": c} for w, c, _ in items[:6]],
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

    # Merge AI results (filter out generic category words the AI might still produce)
    _ai_reject = {
        "韓劇", "日劇", "陸劇", "台劇", "美劇", "追劇", "看劇",
        "電影", "看電影", "動漫", "動畫", "漫畫", "綜藝", "紀錄片",
        "唱歌", "音樂", "聽歌", "聽音樂", "歌手", "樂團",
        "散步", "跑步", "運動", "旅行", "旅遊", "出國",
        "約會", "聚餐", "健身", "游泳", "甜點", "飲料", "咖啡",
    }
    for entry in ai_interests:
        cat = entry.get("category", "")
        if not cat:
            continue
        if cat not in merged:
            merged[cat] = {}
            category_order.append(cat)
        for item in entry.get("items", []):
            name = item["name"] if isinstance(item, dict) else str(item)
            if name in _ai_reject:
                continue
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

    # 批次分詞（jieba）
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

    shared_interests = _extract_shared_interests(all_words_by_person, persons, total_msgs=len(messages))

    return {
        "wordCloud": word_cloud,
        "uniquePhrases": unique_phrases,
        "sharedInterests": shared_interests,
    }
