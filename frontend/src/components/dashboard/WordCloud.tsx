import { Heart } from "lucide-react";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

const PERSON_COLORS = [
  ["#E8457E", "#C4225D", "#F06292", "#E8457ECC", "#AD1457"],
  ["#9F7AEA", "#7C3AED", "#B794F4", "#9F7AEACC", "#6B21A8"],
];

const PILL_STYLES = [
  { bg: "bg-rose-soft", textColor: "text-rose-primary", iconColor: "text-rose-primary" },
  { bg: "bg-purple-soft", textColor: "text-purple-accent", iconColor: "text-purple-accent" },
  { bg: "bg-[#F5A62315]", textColor: "text-gold-accent", iconColor: "text-gold-accent" },
] as const;

function computeFontSize(count: number, maxCount: number, minCount: number): number {
  if (maxCount === minCount) return 18;
  const ratio = (count - minCount) / (maxCount - minCount);
  return Math.round(13 + ratio * 19);
}

export function WordCloud({ result }: Props) {
  const { persons } = result;
  const { wordCloud, uniquePhrases } = result.textAnalysis;
  const topPhrases = uniquePhrases.slice(0, 5);
  const labels = persons.map((p) => `${p} 的高頻詞`);

  return (
    <section className="w-full bg-bg-blush px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      <h2 className="mb-6 sm:mb-8 font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
        文字雲 & 專屬用語
      </h2>

      {/* Word cloud cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5">
        {persons.map((person, personIdx) => {
          const words = wordCloud[person] ?? [];
          const counts = words.map((w) => w.count);
          const maxCount = Math.max(...counts, 1);
          const minCount = Math.min(...counts, 0);
          const colors = PERSON_COLORS[personIdx % PERSON_COLORS.length];
          const dotColor = personIdx === 0 ? "#E8457E" : "#9F7AEA";

          return (
            <div
              key={person}
              className="rounded-[20px] border border-border-light bg-white p-7"
            >
              {/* Person label with dot */}
              <div className="mb-4 flex items-center gap-2">
                <span
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: dotColor }}
                />
                <span className="font-heading text-[16px] font-bold text-text-primary">
                  {labels[personIdx] ?? person}
                </span>
              </div>

              {/* Word display area */}
              <div
                className="flex h-[160px] sm:h-[220px] flex-wrap items-center justify-center gap-x-2 sm:gap-x-3 gap-y-2 overflow-hidden rounded-[12px] sm:rounded-[16px] p-3 sm:p-4"
                style={{ backgroundColor: personIdx === 0 ? "#FFF0F3" : "#EDE4F520" }}
              >
                {words.map((w, wIdx) => (
                  <span
                    key={w.word}
                    className="font-heading font-bold transition-transform hover:scale-110"
                    style={{
                      fontSize: `${computeFontSize(w.count, maxCount, minCount)}px`,
                      color: colors[wIdx % colors.length],
                    }}
                  >
                    {w.word}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Unique phrases pills */}
      {topPhrases.length > 0 && (
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          {topPhrases.map((item, idx) => {
            const style = PILL_STYLES[idx % PILL_STYLES.length];
            return (
              <span
                key={item.phrase}
                className={`inline-flex items-center gap-2 rounded-full px-5 py-2.5 font-body text-[13px] font-semibold ${style.bg} ${style.textColor}`}
              >
                <Heart className={`h-3.5 w-3.5 ${style.iconColor}`} />
                「{item.phrase}」 &times; {item.count} 次
              </span>
            );
          })}
        </div>
      )}
    </section>
  );
}
