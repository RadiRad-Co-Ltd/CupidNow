import { MessageCircle, Type, Smile, Phone, type LucideIcon } from "lucide-react";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

interface StatCard {
  icon: LucideIcon;
  iconBg: string;
  iconColor: string;
  badge: string;
  value: number;
  label: string;
}

export function BasicStatsCards({ result }: Props) {
  const { messageCount, wordCount, typeBreakdown, callStats, dateRange } =
    result.basicStats;
  const persons = result.persons;

  const totalHours = Math.round(callStats.totalDurationSeconds / 3600);
  const avgWordsPerMsg = messageCount.total
    ? Math.round(wordCount.total / messageCount.total)
    : 0;
  const maxCallH = Math.floor(callStats.maxDurationSeconds / 3600);
  const maxCallM = Math.round((callStats.maxDurationSeconds % 3600) / 60);

  const herPct = messageCount.total
    ? Math.round(((messageCount[persons[0]] ?? 0) / messageCount.total) * 100)
    : 50;
  const himPct = 100 - herPct;

  const herStickers = (result.basicStats.personBalance[persons[0]]?.sticker?.count ?? 0);
  const himStickers = (result.basicStats.personBalance[persons[1]]?.sticker?.count ?? 0);
  const stickerWinner = herStickers >= himStickers ? persons[0] : persons[1];

  const cards: StatCard[] = [
    {
      icon: MessageCircle,
      iconBg: "bg-rose-soft",
      iconColor: "text-rose-primary",
      badge: `${persons[0]} ${herPct}% · ${persons[1]} ${himPct}%`,
      value: messageCount.total ?? 0,
      label: "總訊息數",
    },
    {
      icon: Type,
      iconBg: "bg-purple-soft",
      iconColor: "text-purple-accent",
      badge: `平均每則 ${avgWordsPerMsg} 字`,
      value: wordCount.total ?? 0,
      label: "總字數",
    },
    {
      icon: Smile,
      iconBg: "bg-[#F5A62318]",
      iconColor: "text-gold-accent",
      badge: `${stickerWinner}超愛貼圖！`,
      value: (typeBreakdown.sticker ?? 0) + (typeBreakdown.photo ?? 0),
      label: "貼圖 & 圖片",
    },
    {
      icon: Phone,
      iconBg: "bg-[#38B2AC18]",
      iconColor: "text-teal-positive",
      badge: `最長 ${maxCallH}h ${maxCallM}m`,
      value: callStats.totalCalls,
      label: `通話次數 · 總計 ${totalHours} 小時`,
    },
  ];

  return (
    <section className="w-full bg-white px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      {/* Header */}
      <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
        <h2 className="font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
          基礎統計
        </h2>
        <span className="font-body text-[13px] sm:text-[14px] text-text-secondary">
          {dateRange.start} — {dateRange.end} · 共 {dateRange.totalDays} 天
        </span>
      </div>

      {/* Cards grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-5">
        {cards.map((card) => (
          <div
            key={card.label}
            className="flex flex-col gap-2 sm:gap-3 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6"
          >
            {/* Icon row with badge */}
            <div className="flex items-center justify-between">
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${card.iconBg}`}>
                <card.icon className={`h-5 w-5 ${card.iconColor}`} />
              </div>
              <span className="font-body text-[12px] font-medium text-text-secondary">
                {card.badge}
              </span>
            </div>

            {/* Value */}
            <div className="font-heading text-[24px] sm:text-[30px] lg:text-[36px] font-extrabold leading-none text-text-primary">
              {card.value.toLocaleString()}
            </div>

            {/* Label */}
            <div className="font-body text-[14px] font-medium text-text-secondary">
              {card.label}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
