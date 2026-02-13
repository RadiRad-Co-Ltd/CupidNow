import { useState, useMemo, useRef, useEffect, useCallback } from "react";
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

function buildDailyGroups(
  trend: Array<Record<string, string | number>>,
  p1: string,
  p2: string,
): BarGroup[] {
  let lastMonth = "";
  return trend.map((entry) => {
    const period = String(entry.period ?? "");
    const day = period.slice(8, 10).replace(/^0/, "");
    const month = period.slice(5, 7).replace(/^0/, "");
    const showMonth = month !== lastMonth;
    lastMonth = month;
    return {
      label: `${month}/${day}`,
      sublabel: showMonth ? `${period.slice(0, 4)}` : undefined,
      her: Number(entry[p1] ?? 0),
      him: Number(entry[p2] ?? 0),
    };
  });
}

function buildWeeklyGroups(
  trend: Array<Record<string, string | number>>,
  p1: string,
  p2: string,
): BarGroup[] {
  const groups: BarGroup[] = [];
  let weekHer = 0;
  let weekHim = 0;
  let weekStartPeriod = "";
  let lastMonth = "";

  for (let i = 0; i < trend.length; i++) {
    const entry = trend[i];
    const period = String(entry.period ?? "");
    if (!weekStartPeriod) weekStartPeriod = period;
    weekHer += Number(entry[p1] ?? 0);
    weekHim += Number(entry[p2] ?? 0);

    if ((i + 1) % 7 === 0 || i === trend.length - 1) {
      const sm = weekStartPeriod.slice(5, 7).replace(/^0/, "");
      const sd = weekStartPeriod.slice(8, 10).replace(/^0/, "");
      const ed = period.slice(8, 10).replace(/^0/, "");
      const showMonth = sm !== lastMonth;
      lastMonth = sm;
      groups.push({
        label: `${sd}-${ed}`,
        sublabel: showMonth ? `${sm}月` : undefined,
        her: weekHer,
        him: weekHim,
      });
      weekHer = 0;
      weekHim = 0;
      weekStartPeriod = "";
    }
  }
  return groups;
}

function buildMonthlyGroups(
  trend: Array<Record<string, string | number>>,
  p1: string,
  p2: string,
): BarGroup[] {
  const monthMap = new Map<string, { her: number; him: number }>();
  for (const entry of trend) {
    const period = String(entry.period ?? "");
    const monthKey = period.slice(0, 7);
    const existing = monthMap.get(monthKey) ?? { her: 0, him: 0 };
    existing.her += Number(entry[p1] ?? 0);
    existing.him += Number(entry[p2] ?? 0);
    monthMap.set(monthKey, existing);
  }

  const groups: BarGroup[] = [];
  let lastYear = "";
  for (const [monthKey, counts] of monthMap) {
    const [year, m] = monthKey.split("-");
    const showYear = year !== lastYear;
    lastYear = year;
    groups.push({
      label: `${parseInt(m)}月`,
      sublabel: showYear ? year : undefined,
      her: counts.her,
      him: counts.him,
    });
  }
  return groups;
}

const TABS: { key: ViewMode; label: string }[] = [
  { key: "day", label: "日" },
  { key: "week", label: "週" },
  { key: "month", label: "月" },
];

const VISIBLE_BARS: Record<ViewMode, number> = { day: 30, week: 14, month: 12 };

export function TrendChart({ result }: Props) {
  const [view, setView] = useState<ViewMode>("month");
  const { trend } = result.timePatterns;
  const [p1, p2] = result.persons;
  const scrollRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [slotWidth, setSlotWidth] = useState(60);

  const allGroups = useMemo(() =>
    view === "month" ? buildMonthlyGroups(trend, p1, p2)
      : view === "week" ? buildWeeklyGroups(trend, p1, p2)
        : buildDailyGroups(trend, p1, p2),
    [view, trend, p1, p2],
  );

  const maxTotal = Math.max(...allGroups.map((g) => g.her + g.him), 1);
  const maxSingle = Math.max(...allGroups.flatMap((g) => [g.her, g.him]), 1);

  let peakIdx = 0;
  let peakTotal = 0;
  allGroups.forEach((g, i) => {
    const t = g.her + g.him;
    if (t > peakTotal) { peakTotal = t; peakIdx = i; }
  });

  // Calculate slot width based on container width / 7
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width ?? 420;
      setSlotWidth(Math.floor(w / VISIBLE_BARS[view]));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [view]);

  // Scroll to rightmost (most recent) on view change
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      requestAnimationFrame(() => {
        el.scrollLeft = el.scrollWidth;
      });
    }
  }, [view, slotWidth]);

  // Drag to scroll
  const isDragging = useRef(false);
  const dragStartX = useRef(0);
  const dragStartScroll = useRef(0);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    const el = scrollRef.current;
    if (!el) return;
    isDragging.current = true;
    dragStartX.current = e.clientX;
    dragStartScroll.current = el.scrollLeft;
    el.setPointerCapture(e.pointerId);
    el.style.cursor = "grabbing";
  }, []);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDragging.current || !scrollRef.current) return;
    scrollRef.current.scrollLeft = dragStartScroll.current - (e.clientX - dragStartX.current);
  }, []);

  const onPointerUp = useCallback(() => {
    isDragging.current = false;
    if (scrollRef.current) scrollRef.current.style.cursor = "grab";
  }, []);

  const totalWidth = allGroups.length * slotWidth;

  return (
    <div
      ref={containerRef}
      className="rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6 md:px-8"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0">
        <div className="flex flex-col gap-1">
          <h3 className="font-heading text-[16px] sm:text-[18px] font-bold text-text-primary">
            聊天頻率趨勢
          </h3>
          <p className="font-body text-[13px] text-text-secondary">
            粉色為 {p1}、紫色為 {p2} — 左右拖移查看更多
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

      {/* Scrollable chart */}
      <div
        ref={scrollRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        className="mt-4 sm:mt-5 overflow-x-auto select-none"
        style={{ scrollbarWidth: "none", cursor: "grab" }}
      >
        <div
          className="relative rounded-xl"
          style={{
            height: 240,
            backgroundColor: "#FEFAFC",
            width: totalWidth,
          }}
        >
          {/* Bars layer */}
          <div
            className="absolute inset-0 flex items-end"
            style={{ padding: "20px 0 0 0" }}
          >
            {allGroups.map((group, idx) => {
              const total = group.her + group.him;
              const totalH = Math.max(Math.round((total / maxTotal) * 170), 6);
              const herRatio = total > 0 ? group.her / total : 0.5;
              const herH = Math.round(totalH * herRatio);
              const himH = totalH - herH;
              const isPeak = idx === peakIdx;

              return (
                <div
                  key={`${view}-${idx}`}
                  className="flex flex-col items-center"
                  style={{ width: slotWidth, flexShrink: 0 }}
                >
                  {/* Peak badge */}
                  <div className="flex h-5 items-center justify-center">
                    {isPeak && (
                      <span
                        className="rounded-[8px] font-body text-[9px] font-bold text-rose-primary whitespace-nowrap"
                        style={{ backgroundColor: "#FFF0F3", padding: "2px 6px" }}
                      >
                        Peak!
                      </span>
                    )}
                  </div>

                  {/* Stacked bar */}
                  <div className="flex flex-1 items-end justify-center">
                    <div className="flex flex-col rounded-lg overflow-hidden" style={{ width: Math.min(slotWidth * 0.45, 28), opacity: 0.35 }}>
                      <div
                        className="transition-all duration-300"
                        style={{ height: herH, backgroundColor: "#E8457E" }}
                      />
                      <div
                        className="transition-all duration-300"
                        style={{ height: himH, backgroundColor: "#9F7AEA" }}
                      />
                    </div>
                  </div>

                  {/* Label */}
                  <div className="flex h-10 flex-col items-center justify-start pt-1.5">
                    <span
                      className={`font-body text-[10px] sm:text-[11px] font-semibold leading-tight whitespace-nowrap ${isPeak ? "text-rose-primary" : ""}`}
                      style={{ color: isPeak ? undefined : "#B8ADC7" }}
                    >
                      {group.label}
                    </span>
                    {group.sublabel && (
                      <span className="font-body text-[9px] sm:text-[10px] text-text-muted leading-tight">
                        {group.sublabel}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* SVG line overlay */}
          <svg
            className="absolute pointer-events-none"
            style={{ top: 25, left: 0, width: totalWidth, height: 170 }}
          >
            {/* Person 1 line */}
            <polyline
              fill="none"
              stroke="#E8457E"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={allGroups
                .map((g, i) => `${i * slotWidth + slotWidth / 2},${170 - (g.her / maxSingle) * 160}`)
                .join(" ")}
            />
            {/* Person 2 line */}
            <polyline
              fill="none"
              stroke="#9F7AEA"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={allGroups
                .map((g, i) => `${i * slotWidth + slotWidth / 2},${170 - (g.him / maxSingle) * 160}`)
                .join(" ")}
            />
            {/* Dots for person 1 */}
            {allGroups.map((g, i) => (
              <circle
                key={`d1-${i}`}
                cx={i * slotWidth + slotWidth / 2}
                cy={170 - (g.her / maxSingle) * 160}
                r="3"
                fill="#E8457E"
              />
            ))}
            {/* Dots for person 2 */}
            {allGroups.map((g, i) => (
              <circle
                key={`d2-${i}`}
                cx={i * slotWidth + slotWidth / 2}
                cy={170 - (g.him / maxSingle) * 160}
                r="3"
                fill="#9F7AEA"
              />
            ))}
          </svg>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
        <div className="flex items-center gap-2">
          <svg width="16" height="10"><line x1="0" y1="5" x2="16" y2="5" stroke="#E8457E" strokeWidth="2.5" strokeLinecap="round" /><circle cx="8" cy="5" r="2.5" fill="#E8457E" /></svg>
          <span className="font-body text-[13px] font-semibold text-text-secondary">{p1}</span>
        </div>
        <div className="flex items-center gap-2">
          <svg width="16" height="10"><line x1="0" y1="5" x2="16" y2="5" stroke="#9F7AEA" strokeWidth="2.5" strokeLinecap="round" /><circle cx="8" cy="5" r="2.5" fill="#9F7AEA" /></svg>
          <span className="font-body text-[13px] font-semibold text-text-secondary">{p2}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-[3px] opacity-35" style={{ background: "linear-gradient(180deg, #E8457E 50%, #9F7AEA 50%)" }} />
          <span className="font-body text-[13px] font-semibold text-text-secondary">合計</span>
        </div>
      </div>
    </div>
  );
}
