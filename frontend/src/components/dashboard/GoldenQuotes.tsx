import { Heart, Smile, Zap, type LucideIcon } from "lucide-react";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

interface QuoteCategory {
  key: "sweetest" | "funniest" | "mostTouching";
  icon: LucideIcon;
  label: string;
  bgClass: string;
  textColor: string;
}

const CATEGORIES: QuoteCategory[] = [
  {
    key: "sweetest",
    icon: Heart,
    label: "最甜蜜",
    bgClass: "bg-rose-soft",
    textColor: "text-rose-primary",
  },
  {
    key: "funniest",
    icon: Smile,
    label: "最好笑",
    bgClass: "bg-[#F5A62315]",
    textColor: "text-gold-accent",
  },
  {
    key: "mostTouching",
    icon: Zap,
    label: "最心動",
    bgClass: "bg-purple-soft",
    textColor: "text-purple-accent",
  },
];

export function GoldenQuotes({ result }: Props) {
  const goldenQuotes = result.aiAnalysis?.goldenQuotes;

  return (
    <section className="w-full bg-white px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      <h2 className="mb-6 sm:mb-8 font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
        金句賞析
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        {CATEGORIES.map((cat) => {
          const quotes = goldenQuotes?.[cat.key];
          const quote = quotes?.[0];

          return (
            <div
              key={cat.key}
              className="flex flex-col gap-4 rounded-[20px] border border-border-light bg-white p-7"
            >
              {/* Tag pill */}
              <span
                className={`inline-flex w-fit items-center gap-1.5 rounded-full px-3.5 py-1.5 font-body text-[12px] font-semibold ${cat.bgClass} ${cat.textColor}`}
              >
                <cat.icon className="h-3 w-3" /> {cat.label}
              </span>

              {/* Quote text */}
              <p className="font-heading text-[17px] font-semibold leading-[1.7] text-text-primary">
                {quote
                  ? `「${quote.quote}」`
                  : "等待 AI 分析產生金句..."}
              </p>

              {/* Attribution */}
              {quote && (
                <span className="font-body text-[13px] text-text-muted">
                  — {quote.sender}，{quote.date}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
