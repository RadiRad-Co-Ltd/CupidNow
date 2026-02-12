import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

interface QuoteCategory {
  key: "sweetest" | "funniest" | "mostTouching";
  emoji: string;
  label: string;
  bgClass: string;
  textColor: string;
}

const CATEGORIES: QuoteCategory[] = [
  {
    key: "sweetest",
    emoji: "\uD83D\uDC95",
    label: "最甜蜜",
    bgClass: "bg-rose-soft",
    textColor: "text-rose-primary",
  },
  {
    key: "funniest",
    emoji: "\uD83D\uDE02",
    label: "最搞笑",
    bgClass: "bg-gold-accent/15",
    textColor: "text-gold-accent",
  },
  {
    key: "mostTouching",
    emoji: "\uD83D\uDC9C",
    label: "最感動",
    bgClass: "bg-purple-soft",
    textColor: "text-purple-accent",
  },
];

export function GoldenQuotes({ result }: Props) {
  const goldenQuotes = result.aiAnalysis?.goldenQuotes;

  return (
    <section className="w-full bg-white" style={{ padding: "48px 80px" }}>
      <h2 className="mb-6 font-heading text-[24px] font-bold text-text-primary">
        金句賞析
      </h2>

      <div className="grid grid-cols-3 gap-5">
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
                className={`inline-flex w-fit items-center gap-1 rounded-full px-3 py-1 font-body text-[13px] font-semibold ${cat.bgClass} ${cat.textColor}`}
              >
                {cat.emoji} {cat.label}
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
