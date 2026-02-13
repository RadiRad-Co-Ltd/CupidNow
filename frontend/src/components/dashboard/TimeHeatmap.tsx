import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

const HOUR_LABELS = Array.from({ length: 24 }, (_, i) => `${i}`);
const DAY_LABELS = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"];

/** Map a value in [0, max] to a heat opacity on #E8457E. */
function heatColor(value: number, max: number): string {
  if (max === 0 || value === 0) return "#E8457E08";
  const ratio = value / max;
  const alpha = Math.round(0x06 + ratio * (0xff - 0x06));
  return `#E8457E${alpha.toString(16).padStart(2, "0")}`;
}

export function TimeHeatmap({ result }: Props) {
  const { heatmap } = result.timePatterns;

  // Find global max for normalization
  const max = heatmap.reduce((m, row) => Math.max(m, ...row), 0);

  // Find peak cell
  let peakDay = 0;
  let peakHour = 0;
  let peakVal = 0;
  heatmap.forEach((row, di) => {
    row.forEach((v, ci) => {
      if (v > peakVal) {
        peakVal = v;
        peakDay = di;
        peakHour = ci;
      }
    });
  });

  return (
    <div className="rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6 md:px-8">
      {/* Scrollable on mobile */}
      <div className="overflow-x-auto -mx-1">
        <div className="min-w-[560px]">
          {/* Hour labels header — show every 3 hours */}
          <div className="flex items-center gap-[2px] mb-1 pl-10 sm:pl-14">
            {HOUR_LABELS.map((label, i) => (
              <div
                key={i}
                className={`flex-1 text-center font-body text-[9px] sm:text-[10px] font-semibold ${
                  i >= 18 ? "text-text-primary" : "text-text-muted"
                }`}
              >
                {i % 3 === 0 ? label : ""}
              </div>
            ))}
          </div>

          {/* Heatmap rows */}
          <div className="flex flex-col gap-[2px]">
            {heatmap.map((row, dayIdx) => (
              <div key={dayIdx} className="flex items-center gap-[2px]">
                <div className="w-10 sm:w-12 shrink-0 font-body text-[11px] sm:text-[12px] font-semibold text-text-secondary">
                  {DAY_LABELS[dayIdx]}
                </div>
                {row.map((value, colIdx) => (
                  <div
                    key={colIdx}
                    className="h-5 sm:h-7 flex-1 rounded-[3px] sm:rounded-[4px]"
                    style={{ backgroundColor: heatColor(value, max) }}
                    title={`${DAY_LABELS[dayIdx]} ${colIdx}:00-${colIdx}:59：${value} 則`}
                  />
                ))}
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="mt-3 sm:mt-4 flex flex-col sm:flex-row items-start sm:items-center sm:justify-between gap-2 pl-10 sm:pl-14">
            <div className="flex items-center gap-2">
              <span className="font-body text-[11px] sm:text-[12px] text-text-muted">少</span>
              <div
                className="h-3 w-24 sm:w-40 rounded-[6px]"
                style={{
                  background:
                    "linear-gradient(to right, #E8457E08, #E8457E40, #E8457E80, #E8457ECC, #E8457E)",
                }}
              />
              <span className="font-body text-[11px] sm:text-[12px] text-text-muted">多</span>
            </div>
            <span className="font-body text-[12px] sm:text-[13px] font-semibold text-rose-primary">
              最活躍：{DAY_LABELS[peakDay]} {peakHour}:00
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
