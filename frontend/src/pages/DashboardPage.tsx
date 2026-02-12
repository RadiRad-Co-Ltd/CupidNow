import { useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Heart, Share2, Plus } from "lucide-react";
import type { AnalysisResult } from "../types/analysis";
import { LoveScoreHero } from "../components/dashboard/LoveScoreHero";
import { BasicStatsCards } from "../components/dashboard/BasicStatsCards";
import { PersonBalance } from "../components/dashboard/PersonBalance";
import { ReplyBehavior } from "../components/dashboard/ReplyBehavior";
import { TimeHeatmap } from "../components/dashboard/TimeHeatmap";
import { TrendChart } from "../components/dashboard/TrendChart";
import { GoodnightAnalysis } from "../components/dashboard/GoodnightAnalysis";
import { ColdWarTimeline } from "../components/dashboard/ColdWarTimeline";
import { SentimentAnalysis } from "../components/dashboard/SentimentAnalysis";
import { WordCloud } from "../components/dashboard/WordCloud";
import { GoldenQuotes } from "../components/dashboard/GoldenQuotes";
import { ShareCTA } from "../components/dashboard/ShareCTA";

interface Props {
  result: AnalysisResult;
}

export function DashboardPage({ result }: Props) {
  const navigate = useNavigate();
  const reportRef = useRef<HTMLElement>(null);
  const shareCardFnRef = useRef<(() => Promise<void>) | null>(null);

  const handleHeaderShare = useCallback(() => {
    shareCardFnRef.current?.();
  }, []);

  const registerShareFn = useCallback((fn: () => Promise<void>) => {
    shareCardFnRef.current = fn;
  }, []);

  return (
    <div className="min-h-screen bg-bg-page">
      {/* Dashboard Header */}
      <header className="flex items-center justify-between bg-white px-4 sm:px-8 lg:px-20 py-3 sm:py-[18px] border-b border-border-light">
        <div className="flex items-center gap-2">
          <Heart className="h-6 w-6 text-rose-primary" />
          <span className="font-heading text-xl font-extrabold text-text-primary">
            CupidNow
          </span>
        </div>
        <div className="flex items-center gap-2 sm:gap-4">
          <button
            type="button"
            onClick={handleHeaderShare}
            className="inline-flex items-center gap-1.5 sm:gap-2 rounded-full bg-rose-soft px-3 py-2 sm:px-5 sm:py-2.5 text-[12px] sm:text-[13px] font-semibold text-rose-primary"
          >
            <Share2 className="h-4 w-4" />
            <span className="hidden sm:inline">分享報告</span>
            <span className="sm:hidden">分享</span>
          </button>
          <button
            type="button"
            onClick={() => navigate("/")}
            className="inline-flex items-center gap-1.5 sm:gap-2 rounded-full bg-rose-primary px-3 py-2 sm:px-5 sm:py-2.5 text-[12px] sm:text-[13px] font-semibold text-white"
          >
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">新分析</span>
            <span className="sm:hidden">新增</span>
          </button>
        </div>
      </header>

      {/* Main content — captured for report download */}
      <main ref={reportRef}>
        <LoveScoreHero result={result} />
        <BasicStatsCards result={result} />
        <PersonBalance result={result} />
        <ReplyBehavior result={result} />

        {/* Time Patterns */}
        <section className="w-full bg-bg-blush px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
          <h2 className="font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
            時間分析
          </h2>
          <p className="mt-2 font-body text-[14px] text-text-secondary">
            看見你們的聊天節奏：什麼時候最活躍？訊息量如何隨時間變化？
          </p>
          <div className="mt-8 flex flex-col gap-5">
            <TimeHeatmap result={result} />
            <TrendChart result={result} />
          </div>
        </section>

        <GoodnightAnalysis result={result} />
        <ColdWarTimeline result={result} />
        <SentimentAnalysis result={result} />
        <WordCloud result={result} />
        <GoldenQuotes result={result} />
      </main>

      <ShareCTA result={result} reportRef={reportRef} onRegister={registerShareFn} />

      {/* Dashboard Footer */}
      <footer
        className="flex flex-col sm:flex-row items-center justify-between gap-2 px-4 sm:px-8 lg:px-20 py-4 sm:py-6"
        style={{ backgroundColor: "#2D1B33" }}
      >
        <div className="flex items-center gap-2">
          <Heart className="h-[18px] w-[18px] text-rose-primary" />
          <span className="font-heading text-[16px] font-bold text-white">
            CupidNow
          </span>
        </div>
        <span className="font-body text-[10px] sm:text-[12px] text-white/50 text-center">
          Powered by Claude AI · HTTPS 加密 · 分析完即刪除
        </span>
      </footer>
    </div>
  );
}
