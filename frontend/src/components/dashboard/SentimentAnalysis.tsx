import { Sparkles, Heart, Zap, Coffee, Flame, Moon, BarChart3, type LucideIcon } from "lucide-react";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

interface SentimentCategory {
  key: string;
  label: string;
  icon: LucideIcon;
  color: string;
  gradient: string;
}

const SENTIMENT_CATEGORIES: SentimentCategory[] = [
  { key: "sweet", label: "甜到蛀牙", icon: Heart, color: "#E8457E", gradient: "linear-gradient(90deg, #E8457E, #F472B6)" },
  { key: "flirty", label: "曖昧放電", icon: Zap, color: "#9F7AEA", gradient: "linear-gradient(90deg, #9F7AEA, #D6BCFA)" },
  { key: "daily", label: "柴米油鹽", icon: Coffee, color: "#38B2AC", gradient: "linear-gradient(90deg, #38B2AC, #81E6D9)" },
  { key: "conflict", label: "火藥味", icon: Flame, color: "#E87461", gradient: "linear-gradient(90deg, #E87461, #FEB2B2)" },
  { key: "missing", label: "想你ing", icon: Moon, color: "#F5A623", gradient: "linear-gradient(90deg, #F5A623, #FBD38D)" },
];

export function SentimentAnalysis({ result }: Props) {
  const sentiment = result.aiAnalysis?.sentiment;
  const insight = result.aiAnalysis?.insight;
  const advice = result.aiAnalysis?.advice ?? [];

  // Find the dominant emotion
  let topCat = SENTIMENT_CATEGORIES[0];
  let topVal = 0;
  SENTIMENT_CATEGORIES.forEach((cat) => {
    const v = sentiment?.[cat.key] ?? 0;
    if (v > topVal) { topVal = v; topCat = cat; }
  });

  return (
    <section className="w-full bg-white px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      <h2 className="mb-6 sm:mb-8 font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
        AI 情緒分析
      </h2>

      <div className="flex flex-col md:flex-row gap-5">
        {/* Left: Sentiment distribution */}
        <div className="flex-1 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-5 sm:p-7">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-heading text-[16px] font-semibold text-text-primary">
              你們的對話味道
            </h3>
            {topVal > 0 && (
              <span
                className="inline-flex items-center gap-1 rounded-full px-3 py-1 font-body text-[11px] font-bold text-white"
                style={{ backgroundColor: topCat.color }}
              >
                主調：<topCat.icon className="h-3 w-3" /> {topCat.label}
              </span>
            )}
          </div>

          <div className="flex flex-col gap-4">
            {SENTIMENT_CATEGORIES.map((cat) => {
              const value = sentiment?.[cat.key] ?? 0;
              return (
                <div key={cat.key} className="flex items-center gap-3">
                  <span className="w-24 shrink-0 font-body text-[13px] font-medium text-text-secondary flex items-center gap-1.5">
                    <cat.icon className="h-4 w-4" style={{ color: cat.color }} />
                    {cat.label}
                  </span>
                  <div className="relative h-4 flex-1 overflow-hidden rounded-full" style={{ backgroundColor: `${cat.color}12` }}>
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.max(Math.min(value, 100), value > 0 ? 4 : 0)}%`,
                        background: cat.gradient,
                      }}
                    />
                  </div>
                  <span
                    className="w-10 shrink-0 text-right font-body text-[14px] font-bold"
                    style={{ color: value > 0 ? cat.color : "#CBD5E0" }}
                  >
                    {value}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: AI Insight card */}
        <div
          className="flex w-full md:w-[360px] md:shrink-0 flex-col gap-5 rounded-[16px] sm:rounded-[20px] p-5 sm:p-7"
          style={{
            background:
              "linear-gradient(160deg, #E8457E 0%, #9F7AEA 100%)",
            boxShadow: "0 8px 32px 0 #E8457E30",
          }}
        >
          <div className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-white" />
            <h3 className="font-heading text-[18px] font-bold text-white">
              AI 情緒洞察
            </h3>
          </div>
          <p className="font-body text-[14px] leading-[1.7] text-white/[.87]">
            {insight || "上傳對話後，AI 將為你們的聊天做情緒解讀 ✨"}
          </p>
          <div className="flex items-center gap-1.5 rounded-full bg-white/20 px-3.5 py-1.5 w-fit">
            <Sparkles className="h-3 w-3 text-white/70" />
            <span className="font-body text-[12px] font-medium text-white/70">
              Groq AI 深度分析
            </span>
          </div>
        </div>
      </div>

      {/* Advice section */}
      {advice.length > 0 && (
        <div className="mt-5 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-5 sm:p-7">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="h-5 w-5 text-purple-accent" />
            <h3 className="font-heading text-[16px] font-semibold text-text-primary">
              數據悄悄話
            </h3>
          </div>
          <div className="flex flex-col gap-3">
            {advice.map((tip, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 rounded-[12px] p-3.5"
                style={{ backgroundColor: idx < 2 ? "#FFF0F3" : "#F3EDF8" }}
              >
                <span
                  className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full font-body text-[11px] font-bold text-white"
                  style={{ backgroundColor: idx < 2 ? "#E8457E" : "#9F7AEA" }}
                >
                  {idx + 1}
                </span>
                <p className="font-body text-[13px] leading-[1.6] text-text-primary">
                  {tip}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
