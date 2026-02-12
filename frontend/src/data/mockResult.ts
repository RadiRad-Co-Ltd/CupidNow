// Development preview mock data — remove before production
import type { AnalysisResult } from "../types/analysis";

export const mockResult: AnalysisResult = {
  persons: ["小美", "阿明"],
  basicStats: {
    messageCount: { total: 28472, "小美": 15375, "阿明": 13097 },
    wordCount: { total: 512496, "小美": 286998, "阿明": 225498 },
    typeBreakdown: { text: 24625, sticker: 2134, photo: 1713, video: 489 },
    callStats: {
      totalCalls: 186,
      completedCalls: 162,
      missedCalls: 24,
      totalDurationSeconds: 320400,
      avgDurationSeconds: 1978,
      maxDurationSeconds: 9240,
    },
    dateRange: { start: "2024-01-15", end: "2025-02-10", totalDays: 392 },
    personBalance: {
      "小美": {
        text: { count: 13257, percent: 53.8 },
        sticker: { count: 1387, percent: 65.0 },
        photo: { count: 907, percent: 52.9 },
        word: { count: 286998, percent: 56.0 },
        call: { count: 98, percent: 52.7 },
      },
      "阿明": {
        text: { count: 11368, percent: 46.2 },
        sticker: { count: 747, percent: 35.0 },
        photo: { count: 806, percent: 47.1 },
        word: { count: 225498, percent: 44.0 },
        call: { count: 88, percent: 47.3 },
      },
    },
  },
  replyBehavior: {
    instantReplyRate: { "小美": 0.58, "阿明": 0.43 },
    avgReplyTime: { "小美": 120, "阿明": 210 },
    speedDistribution: { "<1m": 42, "1-5m": 26, "5-30m": 19, "30m-1h": 8, ">1h": 5 },
    topicInitiator: { "小美": 412, "阿明": 287 },
  },
  timePatterns: {
    heatmap: [
      [2, 1, 0, 0, 0, 0, 1, 3, 8, 12, 15, 10, 8, 14, 18, 20, 22, 25, 35, 42, 48, 45, 30, 12],
      [3, 1, 0, 0, 0, 0, 1, 4, 10, 14, 12, 8, 10, 16, 20, 22, 28, 32, 40, 48, 50, 47, 35, 15],
      [2, 1, 0, 0, 0, 0, 2, 3, 8, 10, 11, 9, 7, 12, 16, 18, 20, 24, 30, 38, 42, 40, 28, 10],
      [1, 1, 0, 0, 0, 0, 1, 3, 7, 10, 12, 8, 8, 14, 15, 18, 20, 22, 32, 40, 44, 38, 25, 8],
      [4, 2, 1, 0, 0, 0, 1, 5, 8, 12, 10, 9, 10, 15, 18, 22, 28, 35, 45, 50, 48, 42, 30, 14],
      [5, 3, 1, 0, 0, 0, 2, 4, 6, 10, 8, 7, 12, 14, 10, 8, 15, 18, 28, 32, 38, 35, 25, 10],
      [6, 4, 2, 0, 0, 0, 2, 5, 7, 8, 6, 8, 10, 12, 8, 6, 12, 16, 24, 30, 35, 32, 22, 8],
    ],
    trend: [
      { month: "2024-01", "小美": 320, "阿明": 260 },
      { month: "2024-02", "小美": 580, "阿明": 470 },
      { month: "2024-03", "小美": 720, "阿明": 580 },
      { month: "2024-04", "小美": 890, "阿明": 730 },
      { month: "2024-05", "小美": 1280, "阿明": 1050 },
      { month: "2024-06", "小美": 1420, "阿明": 1180 },
      { month: "2024-07", "小美": 1350, "阿明": 1120 },
      { month: "2024-08", "小美": 980, "阿明": 850 },
      { month: "2024-09", "小美": 1150, "阿明": 960 },
      { month: "2024-10", "小美": 1280, "阿明": 1070 },
      { month: "2024-11", "小美": 1450, "阿明": 1210 },
      { month: "2024-12", "小美": 1520, "阿明": 1290 },
      { month: "2025-01", "小美": 1600, "阿明": 1350 },
      { month: "2025-02", "小美": 435, "阿明": 372 },
    ],
    goodnightAnalysis: {
      whoSaysGoodnightFirst: { "小美": 78, "阿明": 22 },
      whoSaysGoodmorningFirst: { "阿明": 65, "小美": 35 },
      avgLastChatTime: 1.383,
    },
  },
  coldWars: [
    { startDate: "2024-03-15", endDate: "2024-03-18", messageDrop: 82 },
    { startDate: "2024-08-02", endDate: "2024-08-05", messageDrop: 45 },
  ],
  textAnalysis: {
    wordCloud: {
      "小美": [
        { word: "哈哈哈", count: 487 },
        { word: "好喔", count: 342 },
        { word: "想你", count: 278 },
        { word: "吃飯了嗎", count: 234 },
        { word: "晚安", count: 212 },
        { word: "寶貝", count: 189 },
        { word: "好累喔", count: 167 },
        { word: "可愛", count: 145 },
        { word: "欸你看", count: 128 },
        { word: "嗚嗚嗚", count: 112 },
      ],
      "阿明": [
        { word: "好的", count: 523 },
        { word: "哈哈", count: 378 },
        { word: "在幹嘛", count: 267 },
        { word: "吃了嗎", count: 223 },
        { word: "晚安", count: 198 },
        { word: "辛苦了", count: 176 },
        { word: "加油", count: 154 },
        { word: "想你", count: 142 },
        { word: "乖", count: 118 },
        { word: "嗯嗯", count: 97 },
      ],
    },
    uniquePhrases: [
      { phrase: "小笨蛋", count: 247 },
      { phrase: "嗚嗚嗚", count: 189 },
      { phrase: "mua～", count: 156 },
      { phrase: "乖乖睡", count: 98 },
      { phrase: "你最棒了", count: 73 },
    ],
  },
  aiAnalysis: {
    loveScore: {
      score: 87,
      comment:
        "你們的對話充滿默契與火花，秒回率極高，深夜時光更是拉近距離的關鍵。",
    },
    sentiment: {
      sweet: 38,
      flirty: 22,
      daily: 28,
      conflict: 4,
      missing: 8,
    },
    goldenQuotes: {
      sweetest: [
        {
          quote: "每天最期待的事就是看到你傳來的訊息，不管多累都會瞬間充滿電。",
          sender: "小美",
          date: "2024-06-15",
        },
      ],
      funniest: [
        {
          quote: "你說你在減肥，結果半夜傳了五張宵夜照片給我，我真的笑到肚子痛。",
          sender: "阿明",
          date: "2024-09-28",
        },
      ],
      mostTouching: [
        {
          quote: "如果時間可以倒轉，我還是會在那天鼓起勇氣跟你說第一句話。",
          sender: "阿明",
          date: "2025-01-01",
        },
      ],
    },
    insight:
      "你們的對話以正面情緒為主基調，日常分享佔了很大比例，代表彼此在對方生活中越來越重要。摩擦比例極低（僅 4%），而且每次低潮都能很快回溫，說明你們的互動品質很高。",
  },
};
