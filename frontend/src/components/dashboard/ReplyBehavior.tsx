import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

/** Format seconds into human-readable Chinese text. */
function formatSeconds(totalSeconds: number): string {
  if (totalSeconds < 0) return "0 秒";

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.round(totalSeconds % 60);

  if (hours > 0) {
    return minutes > 0 ? `${hours} 小時 ${minutes} 分` : `${hours} 小時`;
  }
  if (minutes > 0) {
    return seconds > 0 ? `${minutes} 分 ${seconds} 秒` : `${minutes} 分`;
  }
  return `${seconds} 秒`;
}

const SPEED_LABELS = ["<1分鐘", "1-5分", "5-30分", "30-60分", ">1小時"];

export function ReplyBehavior({ result }: Props) {
  const { replyBehavior, persons } = result;
  const [person1, person2] = persons;

  // --- Instant reply rate bars ---
  const instantRates = [
    {
      name: person1,
      rate: replyBehavior.instantReplyRate[person1] ?? 0,
      color: "#E8457E",
    },
    {
      name: person2,
      rate: replyBehavior.instantReplyRate[person2] ?? 0,
      color: "#9F7AEA",
    },
  ];

  // --- Speed distribution chart data ---
  const speedData = SPEED_LABELS.map((label, idx) => {
    const keys = Object.keys(replyBehavior.speedDistribution);
    return {
      label,
      count: replyBehavior.speedDistribution[keys[idx]] ?? 0,
    };
  });

  // --- Topic initiator ---
  const initiatorEntries = Object.entries(replyBehavior.topicInitiator);
  const topInitiator =
    initiatorEntries.length > 0
      ? initiatorEntries.reduce((a, b) => (a[1] >= b[1] ? a : b))
      : null;

  // --- Who replies faster ---
  const avgEntries = Object.entries(replyBehavior.avgReplyTime);
  const fasterReplier =
    avgEntries.length >= 2
      ? avgEntries.reduce((a, b) => (a[1] <= b[1] ? a : b))
      : null;

  return (
    <section className="bg-white px-[80px] py-[48px]">
      <h2 className="mb-8 font-heading text-[24px] font-bold text-text-primary">
        回覆行為分析
      </h2>

      <div className="grid grid-cols-2 gap-5">
        {/* ---- Left Column ---- */}
        <div className="flex flex-col gap-5">
          {/* Instant reply rate card */}
          <div className="rounded-[20px] border border-border-light bg-white p-7">
            <h3 className="mb-5 font-heading text-base font-bold text-text-primary">
              秒回率
            </h3>
            <div className="flex flex-col gap-4">
              {instantRates.map((item) => {
                const pct = Math.round(item.rate);
                return (
                  <div key={item.name} className="flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-body text-sm font-semibold text-text-primary">
                        {item.name}
                      </span>
                      <span
                        className="font-body text-sm font-bold"
                        style={{ color: item.color }}
                      >
                        {pct}%
                      </span>
                    </div>
                    <div className="h-3 w-full overflow-hidden rounded-full bg-bg-blush">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${pct}%`,
                          backgroundColor: item.color,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Fun stats row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Topic initiator */}
            <div className="rounded-[16px] bg-gradient-to-br from-rose-soft to-purple-soft p-5">
              <p className="mb-1 font-body text-xs font-semibold text-text-muted">
                話題發起王
              </p>
              <p className="font-heading text-lg font-bold text-text-primary">
                {topInitiator ? topInitiator[0] : "—"}
              </p>
              {topInitiator && (
                <p className="mt-1 font-body text-xs text-text-secondary">
                  發起了 {topInitiator[1]} 次話題
                </p>
              )}
            </div>

            {/* Faster replier */}
            <div className="rounded-[16px] bg-gradient-to-br from-purple-soft to-rose-soft p-5">
              <p className="mb-1 font-body text-xs font-semibold text-text-muted">
                閃電回覆手
              </p>
              <p className="font-heading text-lg font-bold text-text-primary">
                {fasterReplier ? fasterReplier[0] : "—"}
              </p>
              {fasterReplier && (
                <p className="mt-1 font-body text-xs text-text-secondary">
                  平均 {formatSeconds(fasterReplier[1])} 回覆
                </p>
              )}
            </div>
          </div>
        </div>

        {/* ---- Right Column ---- */}
        <div className="flex flex-col gap-5">
          {/* Speed distribution chart card */}
          <div className="rounded-[20px] border border-border-light bg-white p-7">
            <h3 className="mb-5 font-heading text-base font-bold text-text-primary">
              回覆速度分布
            </h3>
            <div className="h-[220px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={speedData}
                  margin={{ top: 8, right: 8, left: -12, bottom: 0 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#F3E8EE"
                  />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 11, fill: "#B8ADC7" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#B8ADC7" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 12,
                      border: "1px solid #F3E8EE",
                      fontSize: 13,
                      fontFamily: "Inter",
                    }}
                    cursor={{ fill: "#E8457E10" }}
                  />
                  <Bar
                    dataKey="count"
                    fill="#E8457E"
                    radius={[6, 6, 0, 0]}
                    maxBarSize={40}
                    name="次數"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Average reply time cards */}
          <div className="grid grid-cols-2 gap-4">
            {persons.map((name, idx) => (
              <div
                key={name}
                className="rounded-[16px] border border-border-light bg-white p-5"
              >
                <p className="mb-1 font-body text-xs font-semibold text-text-muted">
                  {name} 平均回覆
                </p>
                <p
                  className="font-heading text-lg font-bold"
                  style={{ color: idx === 0 ? "#E8457E" : "#9F7AEA" }}
                >
                  {formatSeconds(replyBehavior.avgReplyTime[name] ?? 0)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
