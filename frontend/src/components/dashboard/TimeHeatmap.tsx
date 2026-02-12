import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

const TIME_LABELS = [
  "0-3",
  "3-6",
  "6-9",
  "9-12",
  "12-15",
  "15-18",
  "18-21",
  "21-24",
];

const DAY_LABELS = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"];

/** Aggregate a 24-hour row into 8 three-hour buckets. */
function bucketize(row: number[]): number[] {
  if (row.length <= 8) return row;
  const buckets: number[] = [];
  for (let i = 0; i < 8; i++) {
    const start = i * 3;
    buckets.push(
      (row[start] ?? 0) + (row[start + 1] ?? 0) + (row[start + 2] ?? 0)
    );
  }
  return buckets;
}

/** Map a value in [0, max] to a heat opacity on #E8457E. */
function heatColor(value: number, max: number): string {
  if (max === 0 || value === 0) return "#E8457E08";
  const ratio = value / max;
  // Map to hex alpha: 06 → FF
  const alpha = Math.round(0x06 + ratio * (0xff - 0x06));
  return `#E8457E${alpha.toString(16).padStart(2, "0")}`;
}

export function TimeHeatmap({ result }: Props) {
  const { heatmap } = result.timePatterns;
  const bucketed = heatmap.map(bucketize);

  // Find global max for normalization
  const max = bucketed.reduce(
    (m, row) => Math.max(m, ...row),
    0,
  );

  // Find peak cell
  let peakDay = 0;
  let peakCol = 0;
  let peakVal = 0;
  bucketed.forEach((row, di) => {
    row.forEach((v, ci) => {
      if (v > peakVal) {
        peakVal = v;
        peakDay = di;
        peakCol = ci;
      }
    });
  });

  return (
    <div className="rounded-[20px] border border-border-light bg-white p-6" style={{ padding: "24px 32px" }}>
      {/* Time labels header */}
      <div className="flex items-center gap-1 mb-1" style={{ paddingLeft: 56 }}>
        {TIME_LABELS.map((label, i) => (
          <div
            key={label}
            className={`flex-1 text-center font-body text-[11px] font-semibold ${
              i >= 6 ? "text-text-primary" : "text-text-muted"
            }`}
          >
            {label}
          </div>
        ))}
      </div>

      {/* Heatmap rows */}
      <div className="flex flex-col gap-1">
        {bucketed.map((row, dayIdx) => (
          <div key={dayIdx} className="flex items-center gap-1">
            <div className="w-[48px] shrink-0 font-body text-[12px] font-semibold text-text-secondary">
              {DAY_LABELS[dayIdx]}
            </div>
            {row.map((value, colIdx) => (
              <div
                key={colIdx}
                className="h-8 flex-1 rounded-[6px]"
                style={{ backgroundColor: heatColor(value, max) }}
                title={`${DAY_LABELS[dayIdx]} ${TIME_LABELS[colIdx]}：${value} 則`}
              />
            ))}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-between" style={{ paddingLeft: 56 }}>
        <div className="flex items-center gap-2">
          <span className="font-body text-[12px] text-text-muted">少</span>
          <div
            className="h-3 w-40 rounded-[6px]"
            style={{
              background:
                "linear-gradient(to right, #E8457E08, #E8457E40, #E8457E80, #E8457ECC, #E8457E)",
            }}
          />
          <span className="font-body text-[12px] text-text-muted">多</span>
        </div>
        <span className="font-body text-[13px] font-semibold text-rose-primary">
          最活躍：{DAY_LABELS[peakDay]} {TIME_LABELS[peakCol]}
        </span>
      </div>
    </div>
  );
}
