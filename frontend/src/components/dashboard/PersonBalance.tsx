import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

interface BarRowData {
  label: string;
  key: string;
}

const BAR_ROWS: BarRowData[] = [
  { label: "訊息數", key: "messages" },
  { label: "字數", key: "words" },
  { label: "貼圖", key: "stickers" },
];

export function PersonBalance({ result }: Props) {
  const person1 = result.persons[0] ?? "Person 1";
  const person2 = result.persons[1] ?? "Person 2";
  const balance = result.basicStats.personBalance;

  const getPercent = (person: string, key: string): number => {
    return balance?.[key]?.[person]?.percent ?? 50;
  };

  return (
    <section className="w-full bg-bg-blush" style={{ padding: "48px 80px" }}>
      {/* Header */}
      <h2 className="font-heading text-[24px] font-bold text-text-primary">
        你們的互動比重
      </h2>
      <p className="mt-2 font-body text-[14px] text-text-secondary">
        每一項指標中，雙方各佔多少？一眼看出誰更主動
      </p>

      {/* Card */}
      <div className="mt-6 rounded-[20px] border border-border-light bg-white" style={{ padding: "32px 40px" }}>
        {/* Legend */}
        <div className="mb-6 flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-rose-primary" />
            <span className="font-body text-[14px] font-semibold text-text-primary">
              {person1}
            </span>
          </div>
          <span className="font-body text-[14px] text-text-muted">vs</span>
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-purple-accent" />
            <span className="font-body text-[14px] font-semibold text-text-primary">
              {person2}
            </span>
          </div>
        </div>

        {/* Bar rows */}
        <div className="flex flex-col gap-5">
          {BAR_ROWS.map((row) => {
            const p1Pct = getPercent(person1, row.key);
            const p2Pct = getPercent(person2, row.key);

            return (
              <div key={row.key} className="flex items-center gap-4">
                {/* Label */}
                <span className="w-16 shrink-0 font-body text-[14px] font-medium text-text-secondary">
                  {row.label}
                </span>

                {/* Person 1 percentage */}
                <span className="w-12 shrink-0 text-right font-body text-[13px] font-semibold text-rose-primary">
                  {Math.round(p1Pct)}%
                </span>

                {/* Stacked bar */}
                <div className="flex h-3 flex-1 overflow-hidden rounded-full">
                  <div
                    className="h-full bg-rose-primary transition-all duration-500"
                    style={{ width: `${p1Pct}%` }}
                  />
                  <div
                    className="h-full bg-purple-accent transition-all duration-500"
                    style={{ width: `${p2Pct}%` }}
                  />
                </div>

                {/* Person 2 percentage */}
                <span className="w-12 shrink-0 font-body text-[13px] font-semibold text-purple-accent">
                  {Math.round(p2Pct)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
