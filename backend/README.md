# CupidNow Backend

Python FastAPI 後端，負責解析 LINE 聊天記錄並執行所有分析管線。

## 線上版本

https://cupidnow-api.onrender.com

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
    └── ai_analysis.py        # Claude AI 情緒分析

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

透過 Groq API (Llama 3.3 70B Versatile) 分析對話情緒：
- **訊息篩選**：jieba 斷詞過濾無意義訊息（純數字、重複字元、停用詞）
- **情感排序**：SnowNLP 計算每則訊息的情感強度，優先保留情感最濃烈的訊息（最多 500 則）
- **回傳**：心動分數 (0-100)、情緒分布、金句摘錄、深度洞察、聊天建議
- **容錯**：API 失敗時回傳 fallback 結果，不影響其他分析

需設定環境變數 `GROQ_API_KEY`。

### 8. SSE 串流端點 (`analyze-stream`)

`POST /api/analyze-stream` 提供與 `/api/analyze` 相同的分析功能，但透過 Server-Sent Events 串流回傳即時進度，前端使用此端點顯示分析進度條。

## 安全機制

| 機制 | 說明 |
|------|------|
| 速率限制 | 每 IP 每 60 秒最多 10 次請求 |
| 檔案大小限制 | 上傳檔案最大 20MB |
| 記憶體清除 | 解析後立即清除原文與中間資料 |
| 無持久化儲存 | 所有處理在記憶體中完成，不寫入磁碟 |
| CORS 白名單 | 僅允許 `localhost:5173` 與 `CORS_ORIGIN` 指定的域名 |

## 環境變數

| 變數 | 必要 | 說明 |
|------|------|------|
| `GROQ_API_KEY` | 否 | Groq API 金鑰，未設定則跳過 AI 分析 |
| `CORS_ORIGIN` | 生產環境必要 | 允許的前端域名（例如 `https://cupidnow.netlify.app`） |

## 部署

### Render (Docker)

使用 `Dockerfile` 部署至 Render：

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
RUN adduser --disabled-password --gecos '' appuser
COPY app/ app/
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Render 設定：**
- Runtime: Docker
- Root Directory: `backend`
- Health Check Path: `/api/health`

**環境變數（Render 控制台）：**
- `GROQ_API_KEY` — Groq API 金鑰
- `CORS_ORIGIN` — `https://cupidnow.netlify.app`

### CI/CD

推送至 `master` 分支後，Render 自動依 Dockerfile 建置並部署。

**注意**：Render 免費方案在 15 分鐘無流量後會休眠，首次請求需等待冷啟動（約 30-60 秒）。

## 測試

```bash
# 全部測試
python -m pytest tests/ -v

# 單一模組
python -m pytest tests/test_parser.py -v

# 含覆蓋率
python -m pytest tests/ --cov=app --cov-report=term-missing
```

目前共 42 個測試，全部通過。
