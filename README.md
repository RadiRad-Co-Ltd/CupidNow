# CupidNow

CupidNow 是一款 LINE 聊天記錄分析工具，透過 AI 與統計分析，將兩人之間的對話轉化為視覺化的互動報告。

## 功能總覽

- **LINE 對話解析** — 支援 LINE 匯出的 `.txt` 格式，自動辨識訊息、貼圖、照片、通話等類型
- **基礎統計** — 訊息數、字數、貼圖/照片數量、通話統計、互動比重
- **回覆行為分析** — 秒回率、平均回覆時間、回覆速度分布、話題發起者
- **時間模式** — 7x8 聊天熱力圖、月度趨勢圖、晚安/早安分析
- **冷戰偵測** — 基於訊息量變化自動偵測冷戰期間
- **文字分析** — jieba 中文斷詞產生文字雲、雙人專屬用語
- **AI 情緒分析** — Claude API 分析情緒分布、產生金句、深度洞察
- **端對端加密** — 前端 AES-256-GCM 加密，後端解密後分析，分析完立即清除原文

## 技術架構

```
CupidNow/
├── backend/          # Python FastAPI 後端
│   ├── app/
│   │   ├── main.py           # FastAPI 進入點
│   │   ├── routers/
│   │   │   └── analyze.py    # POST /api/analyze 端點
│   │   └── services/
│   │       ├── parser.py         # LINE txt 解析器
│   │       ├── stats.py          # 基礎統計引擎
│   │       ├── reply_analysis.py # 回覆行為分析
│   │       ├── time_patterns.py  # 時間模式分析
│   │       ├── cold_war.py       # 冷戰偵測
│   │       ├── text_analysis.py  # 文字分析 (jieba)
│   │       ├── ai_analysis.py    # Claude AI 分析
│   │       └── encryption.py     # AES-256-GCM 加解密
│   └── tests/                # 39 個測試
├── frontend/         # React + Vite + Tailwind v4 前端
│   └── src/
│       ├── pages/
│       │   ├── UploadPage.tsx    # 上傳頁面
│       │   └── DashboardPage.tsx # 分析報告儀表板
│       ├── components/
│       │   ├── FileDropzone.tsx   # 拖放上傳元件
│       │   └── dashboard/        # 12 個儀表板區塊元件
│       ├── lib/
│       │   └── encryption.ts     # WebCrypto AES-GCM 加密
│       └── types/
│           └── analysis.ts       # TypeScript 型別定義
└── docs/             # 設計文件與規劃文件
```

## 快速開始

### 前置需求

- Python 3.12+
- Node.js 18+
- (選用) Anthropic API Key — 用於 AI 情緒分析

### 安裝與啟動

**1. 後端**

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

啟動開發伺服器：

```bash
uvicorn app.main:app --reload --port 8000
```

若需 AI 分析功能，設定環境變數：

```bash
export ANTHROPIC_API_KEY=your-api-key-here
```

**2. 前端**

```bash
cd frontend
npm install
npm run dev
```

前端將在 `http://localhost:5173` 啟動，API 請求自動代理至後端 `http://localhost:8000`。

### 使用方式

1. 開啟 `http://localhost:5173`
2. 從 LINE 匯出聊天記錄（`.txt` 格式）
3. 拖放或點擊上傳檔案
4. 等待分析完成，自動跳轉至儀表板

## 執行測試

**後端測試（39 個）：**

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

**前端建置驗證：**

```bash
cd frontend
npm run build
```

## API 文件

### `GET /api/health`

健康檢查端點。

**回應：**
```json
{"status": "ok"}
```

### `POST /api/analyze`

分析加密的 LINE 聊天記錄。

**請求（multipart/form-data）：**

| 欄位 | 類型 | 說明 |
|------|------|------|
| `file` | File | AES-256-GCM 加密的聊天記錄檔案 |
| `key` | string | Base64 編碼的 AES-256 金鑰 |
| `skip_ai` | bool | (選用) 設為 `true` 跳過 AI 分析 |

**回應（200）：**

```json
{
  "persons": ["小美", "阿明"],
  "basicStats": {
    "messageCount": {"小美": 120, "阿明": 98, "total": 218},
    "wordCount": {"小美": 3400, "阿明": 2800, "total": 6200},
    "typeBreakdown": {"text": 180, "sticker": 25, "photo": 13},
    "callStats": {
      "totalCalls": 5,
      "completedCalls": 4,
      "missedCalls": 1,
      "totalDurationSeconds": 7200,
      "avgDurationSeconds": 1800,
      "maxDurationSeconds": 3600
    },
    "dateRange": {"start": "2024-01-15", "end": "2024-03-20", "totalDays": 65},
    "personBalance": {
      "messages": {
        "小美": {"count": 120, "percent": 55.0},
        "阿明": {"count": 98, "percent": 45.0}
      }
    }
  },
  "replyBehavior": {
    "instantReplyRate": {"小美": 42.5, "阿明": 38.1},
    "avgReplyTime": {"小美": 180, "阿明": 240},
    "speedDistribution": {"under1min": 50, "1to5min": 30, "5to30min": 15, "30to60min": 3, "over60min": 2},
    "topicInitiator": {"小美": 12, "阿明": 8}
  },
  "timePatterns": {
    "heatmap": [[0,0,0,2,5,3,8,1], "...7 rows x 8 cols"],
    "trend": [{"period": "2024-01", "小美": 60, "阿明": 50}],
    "goodnightAnalysis": {
      "whoSaysGoodnightFirst": {"小美": 15, "阿明": 10},
      "whoSaysGoodmorningFirst": {"阿明": 12, "小美": 8},
      "avgLastChatTime": 23.5
    }
  },
  "coldWars": [
    {"startDate": "2024-02-10", "endDate": "2024-02-14", "messageDrop": 75.0}
  ],
  "textAnalysis": {
    "wordCloud": {
      "小美": [{"word": "哈哈", "count": 45}, {"word": "好啊", "count": 32}],
      "阿明": [{"word": "晚安", "count": 38}, {"word": "想你", "count": 25}]
    },
    "uniquePhrases": [{"phrase": "晚安", "count": 73}]
  },
  "aiAnalysis": {
    "loveScore": {"score": 78, "comment": "你們的互動充滿甜蜜與默契"},
    "sentiment": {"sweet": 35, "flirty": 20, "daily": 30, "conflict": 5, "missing": 10},
    "goldenQuotes": {
      "sweetest": [{"quote": "想你了", "sender": "阿明", "date": "2024-02-14"}],
      "funniest": [{"quote": "你是不是偷吃我的零食", "sender": "小美", "date": "2024-01-20"}],
      "mostTouching": [{"quote": "不管怎樣我都在", "sender": "阿明", "date": "2024-03-01"}]
    },
    "insight": "兩人互動頻繁且正向，阿明較常主動表達思念..."
  }
}
```

**錯誤回應：**

| 狀態碼 | 說明 |
|--------|------|
| 400 | 解密失敗、編碼錯誤、或檔案中無訊息 |

## 安全設計

| 層級 | 機制 |
|------|------|
| 傳輸加密 | 前端使用 WebCrypto API 進行 AES-256-GCM 加密 |
| 金鑰管理 | 每次上傳產生隨機 256-bit 金鑰，Base64 傳輸 |
| 記憶體清除 | 後端解密解析後立即清除明文與解析資料 |
| 無持久化儲存 | 所有處理在記憶體中完成，不寫入磁碟 |
| 無需帳號 | 無使用者認證，無資料留存 |

## 技術棧

### 後端

| 技術 | 用途 |
|------|------|
| Python 3.12 | 執行環境 |
| FastAPI | Web 框架 |
| PyCryptodome | AES-256-GCM 加解密 |
| jieba | 中文斷詞 |
| pandas | 資料處理 |
| Anthropic SDK | Claude AI API |
| pytest + pytest-asyncio | 測試框架 |

### 前端

| 技術 | 用途 |
|------|------|
| React 19 | UI 框架 |
| TypeScript 5.9 | 型別安全 |
| Vite 7 | 建置工具 |
| Tailwind CSS v4 | 樣式系統 |
| Recharts 3 | 圖表視覺化 |
| react-router-dom 7 | 路由管理 |
| WebCrypto API | 客戶端加密 |

## 設計系統

CupidNow 使用自訂 Tailwind v4 主題，色彩系統如下：

| Token | 色碼 | 用途 |
|-------|------|------|
| `rose-primary` | `#E8457E` | 主色、Person 1 標記 |
| `purple-accent` | `#9F7AEA` | 輔色、Person 2 標記 |
| `gold-accent` | `#F5A623` | 強調色 |
| `teal-positive` | `#38B2AC` | 正面指標 |
| `bg-page` | `#FFF8FA` | 頁面背景 |
| `bg-blush` | `#FFF0F3` | 區塊交替背景 |
| `text-primary` | `#2D1F3D` | 主要文字 |
| `text-secondary` | `#7A6B8A` | 次要文字 |

字型：標題使用 Plus Jakarta Sans，內文使用 Inter。

## 儀表板區塊

| 元件 | 說明 |
|------|------|
| `LoveScoreHero` | 深色漸層主視覺，顯示 AI 心動分數 |
| `BasicStatsCards` | 4 欄統計卡片（訊息數、字數、貼圖照片、通話） |
| `PersonBalance` | 堆疊長條圖，顯示雙方互動比重 |
| `ReplyBehavior` | 秒回率長條、回覆速度分布圖、趣味統計卡 |
| `TimeHeatmap` | 7x8 聊天時段熱力圖 |
| `TrendChart` | 月度訊息量趨勢圖 |
| `GoodnightAnalysis` | 深色統計卡（誰先說晚安/早安、平均最晚聊天時間） |
| `ColdWarTimeline` | 冷戰事件時間軸 |
| `SentimentAnalysis` | AI 情緒分布長條 + 深度洞察卡 |
| `WordCloud` | 雙人文字雲 + 專屬用語標籤 |
| `GoldenQuotes` | 三欄金句卡（最甜蜜、最搞笑、最感動） |
| `ShareCTA` | 漸層分享區塊 |

## 授權

Copyright 2026 RadiRad Co., Ltd. All rights reserved.
