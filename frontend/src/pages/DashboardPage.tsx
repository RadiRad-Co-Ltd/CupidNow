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
  return (
    <div className="min-h-screen bg-bg-page">
      {/* Dashboard Header */}
      <header className="flex items-center justify-between bg-white px-20 py-5 border-b border-border-light">
        <span className="font-heading text-2xl font-extrabold text-text-primary">
          💕 CupidNow
        </span>
        <span className="font-body text-[14px] text-text-secondary">
          分析報告
        </span>
      </header>

      {/* Main content sections */}
      <main>
        <LoveScoreHero result={result} />
        <BasicStatsCards result={result} />
        <PersonBalance result={result} />
        <ReplyBehavior result={result} />

        {/* Time Patterns */}
        <section className="w-full bg-bg-blush" style={{ padding: "48px 80px" }}>
          <h2 className="font-heading text-[24px] font-bold text-text-primary">
            時間模式
          </h2>
          <p className="mt-2 font-body text-[14px] text-text-secondary">
            什麼時候聊得最多？訊息量如何變化？
          </p>
          <div className="mt-6 grid grid-cols-2 gap-5">
            <TimeHeatmap result={result} />
            <TrendChart result={result} />
          </div>
        </section>

        <GoodnightAnalysis result={result} />
        <ColdWarTimeline result={result} />
        <SentimentAnalysis result={result} />
        <WordCloud result={result} />
        <GoldenQuotes result={result} />
        <ShareCTA />
      </main>

      {/* Dashboard Footer */}
      <footer className="flex flex-col items-center gap-2 border-t border-border-light bg-white px-20 py-8">
        <span className="font-heading text-lg font-bold text-text-primary">
          💕 CupidNow
        </span>
        <p className="font-body text-[13px] text-text-muted">
          你的資料在分析完成後已安全刪除，我們不會儲存任何聊天內容。
        </p>
        <p className="font-body text-[12px] text-text-muted">
          &copy; {new Date().getFullYear()} CupidNow. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
