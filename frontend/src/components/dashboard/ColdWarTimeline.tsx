import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

const EVENT_COLORS = [
  "bg-rose-soft",
  "bg-gold-accent/15",
  "bg-teal-positive/10",
] as const;

export function ColdWarTimeline({ result }: Props) {
  const { coldWars } = result;

  return (
    <section className="w-full bg-bg-blush" style={{ padding: "48px 80px" }}>
      <h2 className="mb-6 font-heading text-[24px] font-bold text-text-primary">
        冷戰偵測時間軸
      </h2>

      <div className="rounded-[20px] border border-border-light bg-white p-7">
        {/* Timeline bar */}
        <div
          className="mb-6 h-2 w-full rounded-full"
          style={{
            background:
              "linear-gradient(90deg, #E8457E 0%, #9F7AEA 50%, #38B2AC 100%)",
          }}
        />

        {coldWars.length > 0 ? (
          <div className="flex flex-wrap gap-4">
            {coldWars.map((event, idx) => (
              <div
                key={`${event.startDate}-${event.endDate}`}
                className={`flex flex-col gap-2 rounded-[14px] p-4 ${EVENT_COLORS[idx % EVENT_COLORS.length]}`}
              >
                <span className="font-heading text-[14px] font-bold text-text-primary">
                  {event.startDate} — {event.endDate}
                </span>
                <span className="font-body text-[13px] text-text-secondary">
                  訊息量下降 {event.messageDrop}%
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 py-10">
            <span className="text-[40px]">{"\u2705"}</span>
            <span className="font-heading text-[16px] font-semibold text-teal-positive">
              沒有偵測到冷戰期
            </span>
            <span className="font-body text-[13px] text-text-secondary">
              你們的感情穩定又甜蜜！
            </span>
          </div>
        )}
      </div>
    </section>
  );
}
