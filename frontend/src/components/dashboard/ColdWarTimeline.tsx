import { AlertTriangle, TrendingDown, TrendingUp } from "lucide-react";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

const EVENT_STYLES = [
  { bg: "bg-[#E8457E10]", tagColor: "#E8457E", tagLabel: "冷戰期", icon: AlertTriangle },
  { bg: "bg-[#F5A62310]", tagColor: "#F5A623", tagLabel: "低潮期", icon: TrendingDown },
] as const;

export function ColdWarTimeline({ result }: Props) {
  const { coldWars } = result;
  const totalDays = result.basicStats.dateRange.totalDays;

  // Build all cards: cold war events + summary
  const eventCards = coldWars.map((event, idx) => {
    const style = EVENT_STYLES[idx % EVENT_STYLES.length];
    const TagIcon = style.icon;
    const desc = event.messageDrop >= 70
      ? `訊息量下降 ${event.messageDrop}%，回覆時間拉長至 4 小時`
      : `訊息量下降 ${event.messageDrop}%，但很快就恢復了`;
    return (
      <div
        key={`${event.startDate}-${event.endDate}`}
        className={`flex flex-col gap-2 rounded-[14px] p-4 shrink-0 ${style.bg}`}
        style={{ width: "calc(33.333% - 8px)", minWidth: 220 }}
      >
        <div className="flex items-center gap-1.5">
          <TagIcon className="h-3.5 w-3.5" style={{ color: style.tagColor }} />
          <span
            className="font-body text-[12px] font-semibold"
            style={{ color: style.tagColor }}
          >
            {style.tagLabel}
          </span>
        </div>
        <span className="font-body text-[13px] font-semibold text-text-primary">
          {event.startDate} — {event.endDate}
        </span>
        <span className="font-body text-[12px] text-text-secondary">
          {desc}
        </span>
      </div>
    );
  });

  // Summary card always last
  const summaryCard = (
    <div
      key="summary"
      className="flex flex-col gap-2 rounded-[14px] bg-[#38B2AC10] p-4 shrink-0"
      style={{ width: "calc(33.333% - 8px)", minWidth: 220 }}
    >
      <div className="flex items-center gap-1.5">
        <TrendingUp className="h-3.5 w-3.5 text-teal-positive" />
        <span className="font-body text-[12px] font-semibold text-teal-positive">
          整體狀態
        </span>
      </div>
      <span className="font-body text-[13px] font-semibold text-text-primary">
        {coldWars.length === 0 ? "零冷戰！" : "持續升溫中"}
      </span>
      <span className="font-body text-[12px] text-text-secondary">
        {totalDays} 天中{coldWars.length === 0 ? "完全沒有" : `僅 ${coldWars.length} 次`}低潮期，感情狀態{coldWars.length <= 2 ? "非常穩定" : "大致穩定"}
      </span>
    </div>
  );

  const allCards = [...eventCards, summaryCard];

  return (
    <section className="w-full bg-bg-blush px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      <h2 className="mb-6 sm:mb-8 font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
        冷戰偵測時間軸
      </h2>

      <div className="rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-7">
        {/* Timeline bar */}
        <div
          className="mb-5 h-2 w-full overflow-hidden rounded-full"
          style={{ backgroundColor: "#E8457E15" }}
        >
          <div
            className="h-full rounded-full"
            style={{
              background:
                "linear-gradient(90deg, #38B2AC60 0%, #38B2AC 15%, #E8457E 35%, #9F7AEA30 40%, #38B2AC 55%, #38B2AC 70%, #F5A62380 78%, #38B2AC 90%, #38B2AC60 100%)",
            }}
          />
        </div>

        {/* Scrollable event cards — 3 visible */}
        <div
          className="flex gap-3 sm:gap-4 overflow-x-auto pb-2"
          style={{ scrollbarWidth: "thin" }}
        >
          {allCards}
        </div>
      </div>
    </section>
  );
}
