# CupidNow

CupidNow 是一款 LINE 聊天記錄分析工具，透過 AI 與統計分析，將兩人之間的對話轉化為視覺化的互動報告。

## 線上版本

- **前端**：https://cupidnow.netlify.app
- **後端 API**：https://cupidnow-api.onrender.com

## 功能總覽

- **LINE 對話解析** — 支援 LINE 匯出的 `.txt` 格式，自動辨識訊息、貼圖、照片、通話等類型
- **基礎統計** — 訊息數、字數、貼圖/照片數量、通話統計、互動比重
- **回覆行為分析** — 秒回率、平均回覆時間、回覆速度分布、話題發起者
- **時間模式** — 7x8 聊天熱力圖、月度趨勢圖、晚安/早安分析
- **冷戰偵測** — 基於訊息量變化自動偵測冷戰期間
- **文字分析** — jieba 中文斷詞產生文字雲、雙人專屬用語
- **AI 情緒分析** — Groq API (Llama 3.3 70B) 分析情緒分布、產生金句、深度洞察、聊天建議
- **分享功能** — 生成精美分享卡圖片，支援 Web Share API 社群平台分享與 PNG 下載
- **完整報告下載** — 一鍵將整頁儀表板截圖為 PNG 下載

## 技術架構

```
CupidNow/
├── backend/          # Python FastAPI 後端
│   ├── app/
│   │   ├── main.py           # FastAPI 進入點 (CORS + 路由)
│   │   ├── routers/
│   │   │   └── analyze.py    # POST /api/analyze 端點
│   │   └── services/
│   │       ├── parser.py         # LINE txt 解析器
│   │       ├── stats.py          # 基礎統計引擎
│   │       ├── reply_analysis.py # 回覆行為分析
│   │       ├── time_patterns.py  # 時間模式分析
│   │       ├── cold_war.py       # 冷戰偵測
│   │       ├── text_analysis.py  # 文字分析 (jieba)
│   │       └── ai_analysis.py    # Claude AI 分析
│   ├── Dockerfile            # 生產環境容器映像
│   └── tests/                # 42 個測試
├── frontend/         # React + Vite + Tailwind v4 前端
│   ├── src/
│   │   ├── pages/
│   │   │   ├── UploadPage.tsx    # 上傳頁面
│   │   │   └── DashboardPage.tsx # 分析報告儀表板
│   │   ├── components/
│   │   │   ├── FileDropzone.tsx   # 拖放上傳元件
│   │   │   └── dashboard/        # 12 個儀表板區塊元件
│   │   ├── data/
│   │   │   └── mockResult.ts     # 開發用模擬資料
│   │   └── types/
│   │       └── analysis.ts       # TypeScript 型別定義
│   └── public/
│       ├── logo.png              # 品牌 Logo
│       └── _redirects            # Netlify SPA 路由
├── netlify.toml      # Netlify 部署設定
└── docs/             # 設計文件與規劃文件
```

## 快速開始

### 前置需求

- Python 3.12+
- Node.js 18+
- (選用) Groq API Key — 用於 AI 情緒分析

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
export GROQ_API_KEY=your-groq-api-key-here
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

**後端測試（42 個）：**

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

分析 LINE 聊天記錄（同步回應）。

**請求（multipart/form-data）：**

| 欄位 | 類型 | 說明 |
|------|------|------|
| `file` | File | LINE 匯出的 `.txt` 聊天記錄檔案（最大 20MB） |
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
    "insight": "兩人互動頻繁且正向，阿明較常主動表達思念...",
    "advice": [
      "小美可以試著更主動表達想念",
      "阿明的回覆速度很棒，繼續保持！",
      "兩人可以多嘗試深入的話題交流"
    ]
  }
}
```

### `POST /api/analyze-stream`

與 `/api/analyze` 相同的分析功能，但透過 SSE (Server-Sent Events) 串流回傳即時進度。前端使用此端點顯示分析進度條。

**SSE 事件格式：**
```
data: {"progress": 15, "stage": "已解析 1,234 則訊息，計算基礎統計..."}
data: {"progress": 45, "stage": "分析時間模式..."}
data: {"progress": 75, "stage": "AI 正在解讀你們的故事..."}
data: {"progress": 100, "stage": "完成！", "result": { ... }}
```

**錯誤回應：**

| 狀態碼 | 說明 |
|--------|------|
| 400 | 編碼錯誤、或檔案中無訊息 |
| 413 | 檔案超過 20MB |
| 429 | 請求頻率超限（每 IP 每分鐘 10 次） |

## 安全設計

| 機制 | 說明 |
|------|------|
| 速率限制 | 每 IP 每 60 秒最多 10 次請求 |
| 檔案大小限制 | 上傳檔案最大 20MB |
| 記憶體清除 | 解析後立即清除原文與中間資料 |
| 無持久化儲存 | 所有處理在記憶體中完成，不寫入磁碟 |
| 無需帳號 | 無使用者認證，無資料留存 |
| CORS 白名單 | 僅允許指定來源（localhost + 生產域名） |

## 技術棧

### 後端

| 技術 | 用途 |
|------|------|
| Python 3.12 | 執行環境 |
| FastAPI | Web 框架 |
| jieba | 中文斷詞 |
| SnowNLP | 情感強度評分（訊息取樣） |
| Groq SDK | Llama 3.3 70B AI 分析 |
| pytest + pytest-asyncio | 測試框架 |
| Docker | 容器化部署 |

### 前端

| 技術 | 用途 |
|------|------|
| React 19 | UI 框架 |
| TypeScript 5.9 | 型別安全 |
| Vite 7 | 建置工具 |
| Tailwind CSS v4 | 樣式系統 |
| Lucide React | 圖示庫 |
| html-to-image | 分享卡 / 報告截圖生成 |
| react-router-dom 7 | 路由管理 |

## 部署

### 前端 — Netlify

- **URL**：https://cupidnow.netlify.app
- **平台**：Netlify（自動部署）
- **建置設定**：`netlify.toml`
  - Base directory: `frontend`
  - Build command: `npm run build`
  - Publish directory: `dist`
- **SPA 路由**：`_redirects` 與 `netlify.toml` 的 `[[redirects]]` 確保所有路徑導向 `index.html`

**環境變數（Netlify 控制台設定）：**

| 變數 | 說明 |
|------|------|
| `VITE_API_URL` | 後端 API URL（例如 `https://cupidnow-api.onrender.com`） |

### 後端 — Render

- **URL**：https://cupidnow-api.onrender.com
- **平台**：Render（Docker 部署）
- **映像**：`backend/Dockerfile`（Python 3.12-slim）
- **健康檢查**：`GET /api/health`

**環境變數（Render 控制台設定）：**

| 變數 | 必要 | 說明 |
|------|------|------|
| `GROQ_API_KEY` | 否 | Groq API 金鑰，未設定則跳過 AI 分析 |
| `CORS_ORIGIN` | 是 | 前端域名（`https://cupidnow.netlify.app`） |

## CI/CD 流程

```
git push origin master
         │
         ├─── Netlify (前端)
         │    1. 偵測到 master 分支推送
         │    2. 執行 npm run build（在 frontend/ 目錄）
         │    3. 部署 dist/ 到 Netlify CDN
         │    4. 自動生效（通常 30 秒內）
         │
         └─── Render (後端)
              1. 偵測到 master 分支推送
              2. 依 backend/Dockerfile 建置 Docker 映像
              3. 部署新容器至 Render
              4. 健康檢查通過後切換流量（約 2-3 分鐘）
```

**注意**：Render 免費方案在 15 分鐘無流量後會休眠，首次請求需等待冷啟動（約 30-60 秒）。

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
圖示：全面使用 Lucide React 圖示庫。

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
| `ShareCTA` | 分享卡生成 + Web Share API 社群分享 + PNG 下載 |

## 授權

Copyright 2026 RadiRad Co., Ltd. All rights reserved.
