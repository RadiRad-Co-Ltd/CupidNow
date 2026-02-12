# CupidNow Backend

Python FastAPI 後端，負責解密、解析 LINE 聊天記錄，並執行所有分析管線。

## 開發環境

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

啟動開發伺服器：

```bash
uvicorn app.main:app --reload --port 8000
```

執行測試：

```bash
python -m pytest tests/ -v
```

## 目錄結構

```
app/
├── main.py                   # FastAPI 應用進入點 (CORS + 路由)
├── routers/
│   └── analyze.py            # POST /api/analyze 端點
└── services/
    ├── parser.py             # LINE txt 聊天記錄解析器
    ├── stats.py              # 基礎統計引擎
    ├── reply_analysis.py     # 回覆行為分析
    ├── time_patterns.py      # 時間模式分析 (熱力圖 + 趨勢 + 晚安)
    ├── cold_war.py           # 冷戰偵測
    ├── text_analysis.py      # 文字分析 (jieba 中文斷詞)
    ├── ai_analysis.py        # Claude AI 情緒分析
    └── encryption.py         # AES-256-GCM 加解密

tests/
├── conftest.py               # AsyncClient fixture
├── fixtures/
│   ├── sample_chat.txt       # 標準測試聊天記錄
│   └── sample_chat_coldwar.txt  # 冷戰模式測試記錄
├── test_health.py            # 健康檢查 (1 test)
├── test_parser.py            # 解析器 (7 tests)
├── test_stats.py             # 基礎統計 (6 tests)
├── test_reply_analysis.py    # 回覆行為 (4 tests)
├── test_time_patterns.py     # 時間模式 (4 tests)
├── test_cold_war.py          # 冷戰偵測 (3 tests)
├── test_text_analysis.py     # 文字分析 (3 tests)
├── test_encryption.py        # 加解密 (3 tests)
├── test_ai_analysis.py       # AI 分析 (4 tests)
├── test_api_analyze.py       # API 端點 (3 tests)
└── test_integration.py       # 端對端整合 (1 test)
```

## 分析管線

### 1. LINE txt 解析器 (`parser.py`)

解析 LINE 匯出的 `.txt` 格式聊天記錄。

**支援格式：**
- 日期標頭：`2024/01/15（一）`
- 訊息行：`09:00\t小美\t你好` (tab 分隔)
- 多行訊息：接續行以 tab 開頭
- 特殊標記：`[貼圖]`、`[照片]`、`[影片]`、`[檔案]`
- 通話記錄：`09:00\t☎ 通話時間 5:32` 或 `未接來電`

**輸出：**
```python
{
    "messages": [Message(timestamp, sender, content, msg_type)],
    "calls": [CallRecord(timestamp, caller, duration_seconds)],
    "persons": ["小美", "阿明"]
}
```

### 2. 基礎統計 (`stats.py`)

計算每人訊息數、字數、訊息類型分布、通話統計、日期範圍、互動比重。

### 3. 回覆行為分析 (`reply_analysis.py`)

- **秒回率**：60 秒內回覆的比例 (0-100)
- **平均回覆時間**：以秒為單位
- **速度分布**：`under1min` / `1to5min` / `5to30min` / `30to60min` / `over60min`
- **話題發起者**：4 小時以上沉默後首位發話者

### 4. 時間模式 (`time_patterns.py`)

- **熱力圖**：7 (週一~週日) x 8 (3 小時時段) 矩陣
- **月度趨勢**：每月每人訊息數
- **晚安分析**：誰先說晚安/早安、平均最晚聊天時間

### 5. 冷戰偵測 (`cold_war.py`)

基於 14 天滾動平均基線，偵測訊息量下降超過 50% 的期間。

### 6. 文字分析 (`text_analysis.py`)

使用 jieba 中文斷詞，過濾停用詞後產生：
- 每人詞頻 top 80（文字雲資料）
- 雙人共用詞彙 top 20（專屬用語）

### 7. AI 分析 (`ai_analysis.py`)

透過 Claude API (claude-sonnet-4-5-20250929) 分析對話情緒：
- **訊息取樣**：每日最多 8 則代表性訊息，避免 API 成本過高
- **回傳**：心動分數 (0-100)、情緒分布、金句摘錄、深度洞察
- **容錯**：API 失敗時回傳 fallback 結果，不影響其他分析

需設定環境變數 `ANTHROPIC_API_KEY`。

## 加密協定

前後端使用 AES-256-GCM 加密：

```
加密格式: nonce(12 bytes) + ciphertext + tag(16 bytes)
金鑰長度: 256 bits (32 bytes)
金鑰傳輸: Base64 編碼
```

前端使用 WebCrypto API 加密，後端使用 PyCryptodome 解密。兩者的 nonce 長度均為 12 bytes。

## 環境變數

| 變數 | 必要 | 說明 |
|------|------|------|
| `ANTHROPIC_API_KEY` | 否 | Claude API 金鑰，未設定則跳過 AI 分析 |

## 測試

```bash
# 全部測試
python -m pytest tests/ -v

# 單一模組
python -m pytest tests/test_parser.py -v

# 含覆蓋率
python -m pytest tests/ --cov=app --cov-report=term-missing
```

目前共 39 個測試，全部通過。
