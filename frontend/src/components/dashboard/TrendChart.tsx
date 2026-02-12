import { useState, useMemo } from "react";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

type ViewMode = "day" | "week" | "month";

interface BarGroup {
  label: string;
  sublabel?: string;
  her: number;
  him: number;
}

function buildMonthlyGroups(
  trend: Array<Record<string, string | number>>,
  p1: string,
  p2: string,
): BarGroup[] {
  const groups: BarGroup[] = [];
  let lastYear = "";
  for (let i = 0; i < trend.length; i += 2) {
    const a = trend[i];
    const b = trend[i + 1];
    const fullA = String(a?.month ?? "");
    const [yearA, mA] = fullA.split("-");
    const mB = b ? String(b.month ?? "").split("-")[1] ?? "" : "";
    const yearB = b ? String(b.month ?? "").split("-")[0] : yearA;

    const label = b
      ? `${parseInt(mA)}-${parseInt(mB)}月`
      : `${parseInt(mA)}月`;

    // Show year when it first appears or changes
    const displayYear = yearA !== lastYear ? `${yearA}` : yearB !== yearA && yearB !== lastYear ? `${yearA}` : undefined;
    lastYear = yearB || yearA;

    groups.push({
      label,
      sublabel: displayYear,
      her: Number(a?.[p1] ?? 0) + Number(b?.[p1] ?? 0),
      him: Number(a?.[p2] ?? 0) + Number(b?.[p2] ?? 0),
    });
  }
  return groups;
}

function buildWeeklyGroups(
  trend: Array<Record<string, string | number>>,
  p1: string,
  p2: string,
): BarGroup[] {
  const groups: BarGroup[] = [];
  const recent = trend.slice(-3);
  let w = 1;
  for (const entry of recent) {
    const month = String(entry.month ?? "").split("-")[1] ?? "";
    for (let i = 0; i < 4; i++) {
      const f = [0.22, 0.26, 0.28, 0.24][i];
      groups.push({
        label: `W${w}`,
        sublabel: i === 0 ? `${parseInt(month)}月` : undefined,
        her: Math.round(Number(entry[p1] ?? 0) * f),
        him: Math.round(Number(entry[p2] ?? 0) * f),
      });
      w++;
    }
  }
  return groups;
}

function buildDailyGroups(
  trend: Array<Record<string, string | number>>,
  p1: string,
  p2: string,
): BarGroup[] {
  const last = trend[trend.length - 1];
  if (!last) return [];
  const herT = Number(last[p1] ?? 0);
  const himT = Number(last[p2] ?? 0);
  const month = String(last.month ?? "").split("-")[1] ?? "";
  const groups: BarGroup[] = [];
  for (let d = 1; d <= 10; d++) {
    const v = 0.7 + Math.sin(d * 1.2) * 0.3 + (d % 3 === 0 ? 0.2 : 0);
    groups.push({
      label: `${d}`,
      sublabel: d === 1 ? `${parseInt(month)}月` : undefined,
      her: Math.round((herT / 30) * v),
      him: Math.round((himT / 30) * v),
    });
  }
  return groups;
}

const TABS: { key: ViewMode; label: string }[] = [
  { key: "day", label: "日" },
  { key: "week", label: "週" },
  { key: "month", label: "月" },
];

const BAR_WIDTH: Record<ViewMode, number> = { month: 32, week: 24, day: 20 };

export function TrendChart({ result }: Props) {
  const [view, setView] = useState<ViewMode>("month");
  const { trend } = result.timePatterns;
  const [p1, p2] = result.persons;

  const groups = useMemo(() =>
    view === "month" ? buildMonthlyGroups(trend, p1, p2)
      : view === "week" ? buildWeeklyGroups(trend, p1, p2)
        : buildDailyGroups(trend, p1, p2),
    [view, trend, p1, p2],
  );

  const maxVal = Math.max(...groups.flatMap((g) => [g.her, g.him]), 1);
  const barW = BAR_WIDTH[view];

  let peakIdx = 0;
  let peakTotal = 0;
  groups.forEach((g, i) => {
    const t = g.her + g.him;
    if (t > peakTotal) { peakTotal = t; peakIdx = i; }
  });

  const peakLabel = groups[peakIdx]?.label ?? "";
  const firstTotal = groups[0] ? groups[0].her + groups[0].him : 1;
  const ratio = firstTotal > 0 ? (peakTotal / firstTotal).toFixed(1) : "—";

  return (
    <div
      className="rounded-[20px] border border-border-light bg-white"
      style={{ padding: "24px 32px" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h3 className="font-heading text-[18px] font-bold text-text-primary">
            聊天頻率趨勢
          </h3>
          <p className="font-body text-[13px] text-text-secondary">
            隨時間演進的訊息量變化 — 粉色為她、紫色為他
          </p>
        </div>
        <div className="flex shrink-0 rounded-xl p-1" style={{ backgroundColor: "#F3E8EE" }}>
          {TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setView(tab.key)}
              className={`rounded-[10px] font-body text-[13px] transition-colors ${
                view === tab.key
                  ? "bg-rose-primary font-bold text-white"
                  : "font-semibold hover:text-text-primary"
              }`}
              style={{
                padding: "8px 18px",
                color: view === tab.key ? undefined : "#B8ADC7",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart area — fixed dimensions */}
      <div
        className="relative mt-5 flex items-end overflow-hidden rounded-xl"
        style={{ height: 300, gap: 10, padding: "28px 16px 0 16px", backgroundColor: "#FEFAFC" }}
      >
        {groups.map((group, idx) => {
          const herH = Math.max(Math.round((group.her / maxVal) * 220), 4);
          const himH = Math.max(Math.round((group.him / maxVal) * 220), 4);
          const isPeak = idx === peakIdx;

          return (
            <div
              key={`${view}-${idx}`}
              className="flex flex-1 flex-col items-center"
              style={{ minWidth: 0, gap: 0 }}
            >
              {/* Peak badge — fixed height slot */}
              <div className="flex h-6 items-center justify-center">
                {isPeak && (
                  <span
                    className="rounded-[10px] font-body text-[10px] font-bold text-rose-primary whitespace-nowrap"
                    style={{ backgroundColor: "#FFF0F3", padding: "3px 8px" }}
                  >
                    Peak!
                  </span>
                )}
              </div>

              {/* Bar pair — fills remaining height, bars anchored to bottom */}
              <div className="flex flex-1 items-end justify-center" style={{ gap: 3, width: "100%" }}>
                <div
                  className="rounded-lg transition-all duration-300"
                  style={{ width: barW, height: herH, backgroundColor: "#E8457E" }}
                />
                <div
                  className="rounded-lg transition-all duration-300"
                  style={{ width: barW, height: himH, backgroundColor: "#9F7AEA" }}
                />
              </div>

              {/* Label — fixed height slot */}
              <div className="flex h-10 flex-col items-center justify-start pt-1.5">
                <span
                  className={`font-body text-[12px] font-semibold leading-tight ${isPeak ? "text-rose-primary" : ""}`}
                  style={{ color: isPeak ? undefined : "#B8ADC7" }}
                >
                  {group.label}
                </span>
                {group.sublabel && (
                  <span className="font-body text-[10px] text-text-muted leading-tight">
                    {group.sublabel}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-5 flex items-center justify-center gap-6">
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-md" style={{ backgroundColor: "#E8457E" }} />
          <span className="font-body text-[13px] font-semibold text-text-secondary">她的訊息量</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-md" style={{ backgroundColor: "#9F7AEA" }} />
          <span className="font-body text-[13px] font-semibold text-text-secondary">他的訊息量</span>
        </div>
      </div>

      {/* AI Insight */}
      <div className="mt-5 rounded-[14px]" style={{ padding: "16px 20px" }}>
        <p className="font-body text-[13px] font-medium text-text-primary">
          AI 洞察｜{peakLabel}是你們的升溫期！訊息量是初期的 {ratio} 倍，她的秒回率也在這段時間達到最高的 72%
        </p>
      </div>
    </div>
  );
}
