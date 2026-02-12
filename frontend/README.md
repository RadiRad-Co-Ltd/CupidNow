# CupidNow Frontend

React + TypeScript + Vite + Tailwind CSS v4 前端應用。

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
│   ├── UploadPage.tsx        # 首頁：檔案上傳 + 加密 + 進度條
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
├── lib/
│   └── encryption.ts         # WebCrypto AES-256-GCM 加密
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

1. 使用者在 `UploadPage` 選擇 `.txt` 檔案
2. `encryption.ts` 使用 WebCrypto API 產生隨機 AES-256 金鑰並加密檔案
3. 加密檔案 + Base64 金鑰透過 `fetch` POST 至 `/api/analyze`
4. 收到 `AnalysisResult` JSON 後存入 `App.tsx` 的 state
5. 自動導向 `/dashboard`，`DashboardPage` 接收 result props 並渲染所有區塊

### API 代理

`vite.config.ts` 設定了開發代理：

```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
  },
}
```

### 設計系統

所有自訂色彩與字型定義在 `src/index.css` 的 `@theme` 區塊中，使用 Tailwind v4 原生主題機制。元件中直接使用 `bg-rose-primary`、`text-text-primary`、`font-heading` 等 utility class。

### 圖表

使用 Recharts 3 繪製：
- `ReplyBehavior` — 回覆速度分布 BarChart
- `TrendChart` — 月度訊息量分組 BarChart
- `TimeHeatmap` — 自製 CSS grid 熱力圖（非 Recharts）
