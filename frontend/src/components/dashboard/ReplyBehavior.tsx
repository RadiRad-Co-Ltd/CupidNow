import { MessageSquare, EyeOff } from "lucide-react";
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
  { label: "30m-1h", gradient: "linear-gradient(180deg, #38B2AC 0%, #81E6D9 100%)" },
  { label: ">1h", gradient: "linear-gradient(180deg, #A0AEC0 0%, #CBD5E0 100%)" },
];

export function ReplyBehavior({ result }: Props) {
  const { replyBehavior, persons } = result;
  const [person1, person2] = persons;

  // Instant reply rates — backend returns 0-100, use directly
  const her = Math.round(replyBehavior.instantReplyRate[person1] ?? 0);
  const him = Math.round(replyBehavior.instantReplyRate[person2] ?? 0);

  // Speed distribution
  const speedEntries = BAR_STYLES.map((bar) => ({
    ...bar,
    value: replyBehavior.speedDistribution[bar.label] ?? 0,
  }));
  const totalSpeed = speedEntries.reduce((s, e) => s + e.value, 0);
  const maxSpeedPct = totalSpeed > 0
    ? Math.max(...speedEntries.map((e) => (e.value / totalSpeed) * 100))
    : 1;

  // Longest streak
  const streak = replyBehavior.longestStreak;
  const streakCount = streak?.count ?? 0;
  const streakDate = streak?.date ?? "";

  // Left on read
  const lor1 = replyBehavior.leftOnRead?.[person1] ?? 0;
  const lor2 = replyBehavior.leftOnRead?.[person2] ?? 0;
  const lorLeader = lor1 >= lor2 ? person1 : person2;
  const lorCount = Math.max(lor1, lor2);

  return (
    <section className="bg-white px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      <h2 className="mb-6 sm:mb-8 font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
        回覆行為分析
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* ---- Left Column ---- */}
        <div className="flex flex-col gap-5">
          {/* Instant reply rate card — flex-1 to match right column height */}
          <div className="flex-1 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-5 sm:p-7 flex flex-col justify-center">
            <h3 className="mb-6 font-heading text-[16px] font-bold text-text-primary">
              秒回率
            </h3>
            <div className="flex flex-col gap-4">
              {/* Person 1 bar */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-body text-[13px] font-semibold text-text-primary">{person1}</span>
                  <span className="font-body text-[13px] font-bold text-rose-primary">{her}%</span>
                </div>
                <div className="h-3 w-full overflow-hidden rounded-full bg-rose-soft">
                  <div
                    className="h-full rounded-full bg-rose-primary transition-all duration-500"
                    style={{ width: `${Math.min(her, 100)}%` }}
                  />
                </div>
              </div>
              {/* Person 2 bar */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-body text-[13px] font-semibold text-text-primary">{person2}</span>
                  <span className="font-body text-[13px] font-bold text-purple-accent">{him}%</span>
                </div>
                <div className="h-3 w-full overflow-hidden rounded-full" style={{ backgroundColor: "#EDE4F5" }}>
                  <div
                    className="h-full rounded-full bg-purple-accent transition-all duration-500"
                    style={{ width: `${Math.min(him, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Fun stats row */}
          <div className="grid grid-cols-2 gap-3 sm:gap-4">
            {/* Longest streak */}
            <div className="flex flex-col items-center justify-center gap-2 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6">
              <MessageSquare className="h-5 w-5 text-teal-positive" />
              <span className="font-heading text-[24px] sm:text-[32px] font-extrabold leading-none text-teal-positive">
                {streakCount}
              </span>
              <span className="font-body text-[13px] font-medium text-text-secondary text-center">最長連續對話</span>
              <span className="font-body text-[11px] sm:text-[12px] font-medium text-text-muted text-center">
                {streakDate}
              </span>
            </div>
            {/* Left on read */}
            <div className="flex flex-col items-center justify-center gap-2 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6">
              <EyeOff className="h-5 w-5" style={{ color: "#E87461" }} />
              <span className="font-heading text-[24px] sm:text-[32px] font-extrabold leading-none" style={{ color: "#E87461" }}>
                {lorCount}
              </span>
              <span className="font-body text-[13px] font-medium text-text-secondary text-center">已讀不回次數</span>
              <span className="font-body text-[11px] sm:text-[12px] font-medium text-text-muted text-center">
                {lorLeader} 較常已讀不回
              </span>
            </div>
          </div>
        </div>

        {/* ---- Right Column ---- */}
        <div className="flex flex-col gap-5">
          {/* Speed distribution — flex-1 to match left column height */}
          <div className="flex-1 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-5 sm:p-7 flex flex-col">
            <h3 className="mb-5 font-heading text-[16px] font-bold text-text-primary">
              回覆速度分布
            </h3>
            <div className="flex flex-col gap-3" style={{ padding: "0 4px" }}>
              {speedEntries.map((entry) => {
                const pct = totalSpeed > 0 ? (entry.value / totalSpeed) * 100 : 0;
                const widthPct = maxSpeedPct > 0 ? (pct / maxSpeedPct) * 100 : 0;
                return (
                  <div key={entry.label} className="flex items-center gap-3">
                    <span className="w-12 shrink-0 font-body text-[11px] font-semibold text-text-secondary text-right whitespace-nowrap">
                      {entry.label}
                    </span>
                    <div className="flex-1 h-6 rounded-full overflow-hidden" style={{ backgroundColor: "#F5F0FA" }}>
                      <div
                        className="h-full rounded-full transition-all duration-500 flex items-center justify-end pr-2"
                        style={{
                          width: `${Math.max(widthPct, 3)}%`,
                          background: entry.gradient,
                        }}
                      >
                        {pct >= 8 && (
                          <span className="font-body text-[10px] font-bold text-white whitespace-nowrap">
                            {Math.round(pct)}%
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="w-14 shrink-0 font-body text-[11px] font-medium text-text-muted text-left">
                      {Math.round(pct)}% ({entry.value})
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
              <span className="font-body text-[13px] font-medium text-text-secondary text-center">
                {person1} 的平均回覆
              </span>
            </div>
            <div className="flex flex-col items-center justify-center gap-2 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6">
              <span className="font-heading text-[22px] sm:text-[28px] font-extrabold leading-none text-purple-accent">
                {fmtCompact(replyBehavior.avgReplyTime[person2] ?? 0)}
              </span>
              <span className="font-body text-[13px] font-medium text-text-secondary text-center">
                {person2} 的平均回覆
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
