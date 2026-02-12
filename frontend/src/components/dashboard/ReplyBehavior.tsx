import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

/** Format seconds into compact "Xm Ys" style. */
function fmtCompact(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = Math.round(totalSeconds % 60);
  if (m === 0) return `${s}s`;
  return s > 0 ? `${m}m ${s}s` : `${m}m`;
}

const BAR_STYLES = [
  { label: "<1m", gradient: "linear-gradient(180deg, #E8457E 0%, #F472B6 100%)" },
  { label: "1-5m", gradient: "linear-gradient(180deg, #9F7AEA 0%, #B794F4 100%)" },
  { label: "5-30m", gradient: "linear-gradient(180deg, #F5A623 0%, #FBD38D 100%)" },
  { label: "30m-1h", gradient: "#38B2AC60" },
  { label: ">1h", gradient: "#B8ADC740" },
];

export function ReplyBehavior({ result }: Props) {
  const { replyBehavior, persons } = result;
  const [person1, person2] = persons;

  // Instant reply rates (already 0-1 range, display as %)
  const her = Math.round((replyBehavior.instantReplyRate[person1] ?? 0) * 100);
  const him = Math.round((replyBehavior.instantReplyRate[person2] ?? 0) * 100);

  // Speed distribution — get values matching BAR_STYLES labels
  const speedEntries = BAR_STYLES.map((bar) => ({
    ...bar,
    value: replyBehavior.speedDistribution[bar.label] ?? 0,
  }));
  const maxSpeed = Math.max(...speedEntries.map((e) => e.value), 1);

  // Topic initiator
  const herTopics = replyBehavior.topicInitiator[person1] ?? 0;
  const himTopics = replyBehavior.topicInitiator[person2] ?? 0;
  const totalTopics = herTopics + himTopics;
  const topicPct = totalTopics > 0 ? Math.round((herTopics / totalTopics) * 100) : 50;
  const topicLeader = herTopics >= himTopics ? "她" : "他";

  return (
    <section className="bg-white px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      <h2 className="mb-6 sm:mb-8 font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
        回覆行為分析
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* ---- Left Column ---- */}
        <div className="flex flex-col gap-5">
          {/* Instant reply rate card */}
          <div className="rounded-[20px] border border-border-light bg-white p-7">
            <h3 className="mb-6 font-heading text-[16px] font-bold text-text-primary">
              秒回率（60 秒內回覆）
            </h3>
            <div className="flex flex-col gap-4">
              {/* Her bar */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-body text-[13px] font-semibold text-text-primary">她</span>
                  <span className="font-body text-[13px] font-bold text-rose-primary">{her}%</span>
                </div>
                <div className="h-3 w-full overflow-hidden rounded-full bg-rose-soft">
                  <div
                    className="h-full rounded-full bg-rose-primary transition-all duration-500"
                    style={{ width: `${her}%` }}
                  />
                </div>
              </div>
              {/* Him bar */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-body text-[13px] font-semibold text-text-primary">他</span>
                  <span className="font-body text-[13px] font-bold text-purple-accent">{him}%</span>
                </div>
                <div className="h-3 w-full overflow-hidden rounded-full" style={{ backgroundColor: "#EDE4F5" }}>
                  <div
                    className="h-full rounded-full bg-purple-accent transition-all duration-500"
                    style={{ width: `${him}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Fun stats row */}
          <div className="grid grid-cols-2 gap-3 sm:gap-4">
            <div className="flex flex-col items-center justify-center gap-2 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6">
              <span className="font-heading text-[24px] sm:text-[32px] font-extrabold leading-none" style={{ color: "#E87461" }}>
                {totalTopics}
              </span>
              <span className="font-body text-[13px] font-medium text-text-secondary">話題發起次數</span>
              <span className="font-body text-[12px] font-medium text-text-muted">
                她 {herTopics} · 他 {himTopics}
              </span>
            </div>
            <div className="flex flex-col items-center justify-center gap-2 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6">
              <span className="font-heading text-[24px] sm:text-[32px] font-extrabold leading-none text-teal-positive">
                {topicPct}%
              </span>
              <span className="font-body text-[13px] font-medium text-text-secondary">
                {topicLeader}先開話題
              </span>
              <span className="font-body text-[12px] font-medium text-text-muted">
                沉默後先發訊息
              </span>
            </div>
          </div>
        </div>

        {/* ---- Right Column ---- */}
        <div className="flex flex-col gap-5">
          {/* Speed distribution — custom CSS bars */}
          <div className="rounded-[20px] border border-border-light bg-white p-7">
            <h3 className="mb-5 font-heading text-[16px] font-bold text-text-primary">
              回覆速度分布
            </h3>
            <div className="flex items-end gap-3" style={{ height: 180, padding: "0 8px" }}>
              {speedEntries.map((entry) => {
                const heightPct = (entry.value / maxSpeed) * 100;
                return (
                  <div key={entry.label} className="flex flex-1 flex-col items-center justify-end gap-2 h-full">
                    <div
                      className="w-full rounded-t-[10px] rounded-b-[4px] transition-all duration-500"
                      style={{
                        height: `${Math.max(heightPct, 5)}%`,
                        background: entry.gradient,
                      }}
                    />
                    <span className="font-body text-[11px] font-semibold text-text-secondary">
                      {entry.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Average reply time cards */}
          <div className="grid grid-cols-2 gap-3 sm:gap-4">
            <div className="flex flex-col items-center justify-center gap-2 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6">
              <span className="font-heading text-[22px] sm:text-[28px] font-extrabold leading-none text-rose-primary">
                {fmtCompact(replyBehavior.avgReplyTime[person1] ?? 0)}
              </span>
              <span className="font-body text-[13px] font-medium text-text-secondary">
                她的平均回覆
              </span>
            </div>
            <div className="flex flex-col items-center justify-center gap-2 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6">
              <span className="font-heading text-[22px] sm:text-[28px] font-extrabold leading-none text-purple-accent">
                {fmtCompact(replyBehavior.avgReplyTime[person2] ?? 0)}
              </span>
              <span className="font-body text-[13px] font-medium text-text-secondary">
                他的平均回覆
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
