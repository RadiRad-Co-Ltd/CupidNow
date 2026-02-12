import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

interface StatCard {
  emoji: string;
  value: number;
  label: string;
}

export function BasicStatsCards({ result }: Props) {
  const { messageCount, wordCount, typeBreakdown, callStats, dateRange } =
    result.basicStats;

  const totalHours = Math.round((callStats.totalDurationSeconds / 3600) * 10) / 10;

  const cards: StatCard[] = [
    {
      emoji: "\uD83D\uDCAC",
      value: messageCount.total ?? 0,
      label: "總訊息數",
    },
    {
      emoji: "\u270D\uFE0F",
      value: wordCount.total ?? 0,
      label: "總字數",
    },
    {
      emoji: "\uD83C\uDFA8",
      value: (typeBreakdown.sticker ?? 0) + (typeBreakdown.photo ?? 0),
      label: "貼圖 & 圖片",
    },
    {
      emoji: "\uD83D\uDCDE",
      value: callStats.totalCalls,
      label: `通話次數 \u00B7 總計 ${totalHours} 小時`,
    },
  ];

  return (
    <section className="w-full bg-white" style={{ padding: "48px 80px" }}>
      {/* Header */}
      <div className="mb-6 flex items-baseline gap-4">
        <h2 className="font-heading text-[24px] font-bold text-text-primary">
          基礎統計
        </h2>
        <span className="font-body text-[14px] text-text-secondary">
          {dateRange.start} — {dateRange.end} · 共 {dateRange.totalDays} 天
        </span>
      </div>

      {/* Cards grid */}
      <div className="grid grid-cols-4 gap-5">
        {cards.map((card) => (
          <div
            key={card.label}
            className="rounded-[20px] border border-border-light bg-white p-6"
          >
            {/* Icon row */}
            <div className="mb-3 text-[28px]">{card.emoji}</div>

            {/* Value */}
            <div className="font-heading text-[36px] font-extrabold text-text-primary">
              {card.value.toLocaleString()}
            </div>

            {/* Label */}
            <div className="mt-1 font-body text-[14px] font-medium text-text-secondary">
              {card.label}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
