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

const DAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"];

/** Map a value in [0, max] to one of the heat colors. */
function heatColor(value: number, max: number): string {
  if (max === 0 || value === 0) return "#F3E8EE";

  const ratio = value / max;

  if (ratio < 0.25) return "#FDDEE8";
  if (ratio < 0.55) return "#E8457E60";
  return "#E8457E";
}

export function TimeHeatmap({ result }: Props) {
  const { heatmap } = result.timePatterns;

  // Find global max for normalization
  const max = heatmap.reduce(
    (m, row) => Math.max(m, ...row),
    0,
  );

  return (
    <div className="rounded-[20px] border border-border-light bg-white px-8 py-6">
      <h3 className="mb-5 font-heading text-base font-bold text-text-primary">
        聊天時段熱力圖
      </h3>

      <div className="flex flex-col gap-1.5">
        {/* Header row with time labels */}
        <div className="flex items-center">
          {/* Spacer for day label column */}
          <div className="w-8 shrink-0" />
          <div className="grid flex-1 grid-cols-8 gap-1.5">
            {TIME_LABELS.map((label) => (
              <div
                key={label}
                className="text-center font-body text-[11px] font-semibold text-text-muted"
              >
                {label}
              </div>
            ))}
          </div>
        </div>

        {/* Heatmap rows */}
        {heatmap.map((row, dayIdx) => (
          <div key={dayIdx} className="flex items-center">
            {/* Day label */}
            <div className="w-8 shrink-0 text-center font-body text-[12px] font-semibold text-text-secondary">
              {DAY_LABELS[dayIdx]}
            </div>
            {/* Cells */}
            <div className="grid flex-1 grid-cols-8 gap-1.5">
              {row.map((value, colIdx) => (
                <div
                  key={colIdx}
                  className="aspect-square w-full rounded-[6px] transition-colors duration-300"
                  style={{ backgroundColor: heatColor(value, max) }}
                  title={`${DAY_LABELS[dayIdx]} ${TIME_LABELS[colIdx]}：${value} 則訊息`}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-5 flex items-center justify-center gap-2">
        <span className="font-body text-[11px] text-text-muted">少</span>
        <div
          className="h-3 w-32 rounded-full"
          style={{
            background:
              "linear-gradient(to right, #F3E8EE, #FDDEE8, #E8457E99, #E8457E)",
          }}
        />
        <span className="font-body text-[11px] text-text-muted">多</span>
      </div>
    </div>
  );
}
