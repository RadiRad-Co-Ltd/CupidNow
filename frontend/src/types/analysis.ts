export interface AnalysisResult {
  persons: string[];
  basicStats: BasicStats;
  replyBehavior: ReplyBehavior;
  timePatterns: TimePatterns;
  coldWars: ColdWarEvent[];
  textAnalysis: TextAnalysis;
  aiAnalysis?: AIAnalysis;
}

export interface BasicStats {
  messageCount: Record<string, number>;
  wordCount: Record<string, number>;
  typeBreakdown: Record<string, number>;
  callStats: {
    totalCalls: number;
    completedCalls: number;
    missedCalls: number;
    totalDurationSeconds: number;
    avgDurationSeconds: number;
    maxDurationSeconds: number;
  };
  dateRange: { start: string; end: string; totalDays: number };
  personBalance: Record<string, Record<string, { count: number; percent: number }>>;
}

export interface ReplyBehavior {
  instantReplyRate: Record<string, number>;
  avgReplyTime: Record<string, number>;
  speedDistribution: Record<string, number>;
  longestStreak: { count: number; date: string };
  leftOnRead: Record<string, number>;
}

export interface TimePatterns {
  heatmap: number[][];
  trend: Array<Record<string, string | number>>;
  goodnightAnalysis: {
    whoSaysGoodnightFirst: Record<string, number>;
    whoSaysGoodmorningFirst: Record<string, number>;
    avgLastChatTime: number;
    avgBedtimeChatMinutes: number;
    bedtimeChatCount: number;
  };
}

export interface ColdWarEvent {
  startDate: string;
  endDate: string;
  messageDrop: number;
}

export interface TextAnalysis {
  wordCloud: Record<string, Array<{ word: string; count: number }>>;
  uniquePhrases: Array<{ phrase: string; count: number }>;
}

export interface AIAnalysis {
  loveScore: { score: number; comment: string };
  sentiment: Record<string, number>;
  goldenQuotes: {
    sweetest: Quote[];
    funniest: Quote[];
    mostTouching: Quote[];
  };
  insight: string;
  sharedInterests?: SharedInterest[];
  advice?: string[];
}

export interface SharedInterest {
  category: string;
  items: SharedInterestItem[] | string[];
}

export interface SharedInterestItem {
  name: string;
  count: number;
}

interface Quote {
  quote: string;
  sender: string;
  date: string;
}
