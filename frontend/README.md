# CupidNow Frontend

React + TypeScript + Vite + Tailwind CSS v4 前端應用。

## 線上版本

https://cupidnow.netlify.app

## 開發環境

```bash
npm install
npm run dev        # 開發伺服器 (http://localhost:5173)
npm run build      # 生產建置 (tsc + vite)
npm run lint       # ESLint 檢查
npm run preview    # 預覽生產建置
```

## 目錄結構

```
src/
├── pages/
│   ├── UploadPage.tsx        # 首頁：檔案上傳 + 進度條
│   └── DashboardPage.tsx     # 儀表板：組合所有分析區塊
├── components/
│   ├── FileDropzone.tsx      # 拖放上傳元件
│   └── dashboard/            # 儀表板區塊元件 (12 個)
│       ├── LoveScoreHero.tsx
│       ├── BasicStatsCards.tsx
│       ├── PersonBalance.tsx
│       ├── ReplyBehavior.tsx
│       ├── TimeHeatmap.tsx
│       ├── TrendChart.tsx
│       ├── GoodnightAnalysis.tsx
│       ├── ColdWarTimeline.tsx
│       ├── SentimentAnalysis.tsx
│       ├── WordCloud.tsx
│       ├── GoldenQuotes.tsx
│       └── ShareCTA.tsx
├── data/
│   └── mockResult.ts         # 開發用模擬資料（可直接預覽儀表板）
├── types/
│   └── analysis.ts           # API 回應型別定義
├── App.tsx                    # 路由設定
├── main.tsx                   # 進入點
└── index.css                  # Tailwind v4 主題設定
```

## 架構說明

### 路由

| 路徑 | 頁面 | 說明 |
|------|------|------|
| `/` | `UploadPage` | 檔案上傳頁面 |
| `/dashboard` | `DashboardPage` | 分析結果儀表板（無資料時重導至 `/`） |

### 資料流

1. 使用者在 `UploadPage` 選擇 `.txt` 檔案（最大 20MB）
2. 頁面載入時自動 ping `/api/health` 暖機後端（Render 免費方案有冷啟動延遲）
3. 透過 `fetch` POST 至 `/api/analyze-stream`（SSE 串流），即時顯示分析進度
4. 收到最終 `result` 事件後存入 `App.tsx` 的 state
5. 自動導向 `/dashboard`，`DashboardPage` 接收 result props 並渲染所有區塊

### 開發預覽

`App.tsx` 預設載入 `src/data/mockResult.ts` 的模擬資料，直接訪問 `/dashboard` 即可預覽儀表板排版，無需啟動後端。

### API 代理

`vite.config.ts` 設定了開發代理：

```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
  },
}
```

生產環境使用 `VITE_API_URL` 環境變數指向後端 API。

### 設計系統

所有自訂色彩與字型定義在 `src/index.css` 的 `@theme` 區塊中，使用 Tailwind v4 原生主題機制。元件中直接使用 `bg-rose-primary`、`text-text-primary`、`font-heading` 等 utility class。

### 圖示

全面使用 [Lucide React](https://lucide.dev) 圖示庫，取代 Unicode emoji。常用圖示包括 `Heart`、`Flame`、`Sparkles`、`Download`、`MessageCircle`、`Moon` 等。

### 圖表

使用自製 CSS 元件繪製（不依賴外部圖表庫）：
- `ReplyBehavior` — CSS 長條圖
- `TrendChart` — CSS 長條圖
- `TimeHeatmap` — CSS grid 熱力圖
- `PersonBalance` — CSS 堆疊長條圖
- `SentimentAnalysis` — CSS 長條圖

### 分享與下載

`ShareCTA` 元件提供三種功能：

| 功能 | 觸發方式 | 技術 |
|------|---------|------|
| 社群分享 | Header「分享報告」按鈕 | Web Share API（含 PNG 檔案）；不支援時 fallback 為下載 |
| 下載分享卡 | 底部「下載分享卡」按鈕 | `html-to-image` 截圖隱藏的分享卡元素 |
| 下載完整報告 | 底部「下載完整報告」按鈕 | `html-to-image` 截圖整個儀表板 `<main>` |

分享卡為一個始終渲染但 `position: absolute; left: -9999` 的離屏 `<div>`，使用 `html-to-image` 的 `toPng()` 生成 PNG。首次呼叫為字型暖機，第二次才正式截圖。

## 部署

### Netlify

已透過 `netlify.toml` 設定自動部署：

```toml
[build]
  base = "frontend"
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

**環境變數（Netlify 控制台）：**

| 變數 | 說明 |
|------|------|
| `VITE_API_URL` | 後端 API URL（例如 `https://cupidnow-api.onrender.com`） |

### CI/CD

推送至 `master` 分支後，Netlify 自動建置並部署。

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| React | 19 | UI 框架 |
| TypeScript | 5.9 | 型別安全 |
| Vite | 7 | 建置工具 |
| Tailwind CSS | v4 | 樣式系統 |
| Lucide React | 0.563+ | 圖示庫 |
| html-to-image | 1.11+ | 分享卡 / 報告截圖 |
| react-router-dom | 7 | 路由管理 |
