import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

interface BarRow {
  label: string;
  herCount: number;
  herPct: number;
  himCount: number;
  himPct: number;
  showCounts: boolean;
}

export function PersonBalance({ result }: Props) {
  const [person1, person2] = result.persons;
  const bal = result.basicStats.personBalance;
  const topic = result.replyBehavior.topicInitiator;

  const get = (person: string, key: string) => bal?.[person]?.[key] ?? { count: 0, percent: 50 };

  // Compute topic initiator percentages
  const herTopics = topic[person1] ?? 0;
  const himTopics = topic[person2] ?? 0;
  const totalTopics = herTopics + himTopics || 1;
  const herTopicPct = Math.round((herTopics / totalTopics) * 100);

  const rows: BarRow[] = [
    {
      label: "訊息數量",
      herCount: get(person1, "text").count,
      herPct: get(person1, "text").percent,
      himCount: get(person2, "text").count,
      himPct: get(person2, "text").percent,
      showCounts: true,
    },
    {
      label: "總字數",
      herCount: get(person1, "word").count,
      herPct: get(person1, "word").percent,
      himCount: get(person2, "word").count,
      himPct: get(person2, "word").percent,
      showCounts: true,
    },
    {
      label: "貼圖 & 圖片",
      herCount: get(person1, "sticker").count + (get(person1, "photo")?.count ?? 0),
      herPct: get(person1, "sticker").percent,
      himCount: get(person2, "sticker").count + (get(person2, "photo")?.count ?? 0),
      himPct: get(person2, "sticker").percent,
      showCounts: true,
    },
    {
      label: "話題發起",
      herCount: herTopics,
      herPct: herTopicPct,
      himCount: himTopics,
      himPct: 100 - herTopicPct,
      showCounts: false,
    },
    {
      label: "語音通話發起",
      herCount: get(person1, "call").count,
      herPct: get(person1, "call").percent,
      himCount: get(person2, "call").count,
      himPct: get(person2, "call").percent,
      showCounts: false,
    },
  ];

  return (
    <section className="w-full bg-bg-blush px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      <h2 className="font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
        你們的互動比重
      </h2>
      <p className="mt-2 font-body text-[14px] text-text-secondary">
        每一項指標中，雙方各佔多少？一眼看出誰更主動
      </p>

      <div
        className="mt-6 sm:mt-8 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6 md:px-10 md:py-8"
      >
        {/* Legend */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-rose-primary" />
            <span className="font-body text-[15px] font-bold text-rose-primary">{person1}</span>
          </div>
          <span className="font-heading text-[14px] font-semibold text-text-muted">vs</span>
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-purple-accent" />
            <span className="font-body text-[15px] font-bold text-purple-accent">{person2}</span>
          </div>
        </div>

        {/* Bar rows */}
        <div className="flex flex-col gap-5">
          {rows.map((row) => {
            const herPct = Math.round(row.herPct);
            const himPct = Math.round(row.himPct);
            const valText = row.showCounts
              ? `${row.herCount.toLocaleString()} (${herPct}%) · ${row.himCount.toLocaleString()} (${himPct}%)`
              : `${herPct}% · ${himPct}%`;

            return (
              <div key={row.label} className="flex flex-col gap-2">
                {/* Header: label left, values right */}
                <div className="flex items-center justify-between">
                  <span className="font-body text-[13px] font-semibold text-text-primary">
                    {row.label}
                  </span>
                  <span className="font-body text-[12px] font-medium text-text-secondary">
                    {valText}
                  </span>
                </div>
                {/* Stacked gradient bar */}
                <div className="flex h-7 gap-[3px] overflow-hidden rounded-full">
                  <div
                    className="h-full rounded-l-full rounded-r-[4px] transition-all duration-500"
                    style={{
                      width: `${herPct}%`,
                      background: "linear-gradient(90deg, #E8457E 0%, #F472B6 100%)",
                    }}
                  />
                  <div
                    className="h-full rounded-l-[4px] rounded-r-full transition-all duration-500"
                    style={{
                      width: `${himPct}%`,
                      background: "linear-gradient(90deg, #9F7AEA 0%, #B794F4 100%)",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
