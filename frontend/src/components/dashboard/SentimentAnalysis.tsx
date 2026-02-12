import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

interface SentimentCategory {
  key: string;
  label: string;
  color: string;
}

const SENTIMENT_CATEGORIES: SentimentCategory[] = [
  { key: "sweet", label: "甜蜜", color: "#E8457E" },
  { key: "flirty", label: "曖昧", color: "#9F7AEA" },
  { key: "daily", label: "日常", color: "#38B2AC" },
  { key: "conflict", label: "衝突", color: "#FF7E7E" },
  { key: "missing", label: "思念", color: "#F5A623" },
];

export function SentimentAnalysis({ result }: Props) {
  const sentiment = result.aiAnalysis?.sentiment;
  const insight = result.aiAnalysis?.insight;

  return (
    <section className="w-full bg-white" style={{ padding: "48px 80px" }}>
      <h2 className="mb-6 font-heading text-[24px] font-bold text-text-primary">
        AI 情緒分析
      </h2>

      <div className="flex gap-5">
        {/* Left: Sentiment distribution */}
        <div className="flex-1 rounded-[20px] border border-border-light bg-white p-7">
          <h3 className="mb-5 font-heading text-[16px] font-semibold text-text-primary">
            情緒分布
          </h3>

          <div className="flex flex-col gap-4">
            {SENTIMENT_CATEGORIES.map((cat) => {
              const value = sentiment?.[cat.key] ?? 0;
              return (
                <div key={cat.key} className="flex items-center gap-3">
                  <span className="w-10 shrink-0 font-body text-[13px] font-medium text-text-secondary">
                    {cat.label}
                  </span>
                  <div className="relative h-3 flex-1 overflow-hidden rounded-full bg-gray-100">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(value, 100)}%`,
                        backgroundColor: cat.color,
                      }}
                    />
                  </div>
                  <span className="w-12 shrink-0 text-right font-body text-[13px] font-semibold text-text-primary">
                    {value}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: AI Insight card */}
        <div
          className="flex w-[360px] shrink-0 flex-col gap-4 rounded-[20px] p-7"
          style={{
            background:
              "linear-gradient(160deg, #E8457E 0%, #9F7AEA 100%)",
            boxShadow: "0 8px 32px 0 #E8457E30",
          }}
        >
          <h3 className="font-heading text-[16px] font-semibold text-white">
            {"\u2728"} AI 深度洞察
          </h3>
          <p className="font-body text-[14px] leading-relaxed text-white/90">
            {insight || "等待 AI 分析..."}
          </p>
        </div>
      </div>
    </section>
  );
}
