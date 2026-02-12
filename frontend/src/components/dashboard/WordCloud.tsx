import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

const PERSON_COLORS = [
  // person1: rose tones
  ["#E8457E", "#C4225D", "#F06292", "#E8457ECC", "#AD1457"],
  // person2: purple tones
  ["#9F7AEA", "#7C3AED", "#B794F4", "#9F7AEACC", "#6B21A8"],
];

const PILL_BG_CLASSES = [
  "bg-rose-soft",
  "bg-purple-soft",
  "bg-gold-accent/15",
] as const;

function computeFontSize(
  count: number,
  maxCount: number,
  minCount: number,
): number {
  if (maxCount === minCount) return 18;
  const ratio = (count - minCount) / (maxCount - minCount);
  return Math.round(13 + ratio * 19); // 13px to 32px
}

export function WordCloud({ result }: Props) {
  const { persons } = result;
  const { wordCloud, uniquePhrases } = result.textAnalysis;
  const topPhrases = uniquePhrases.slice(0, 5);

  return (
    <section className="w-full bg-bg-blush" style={{ padding: "48px 80px" }}>
      <h2 className="mb-6 font-heading text-[24px] font-bold text-text-primary">
        文字雲 & 專屬用語
      </h2>

      {/* Word cloud cards */}
      <div className="grid grid-cols-2 gap-5">
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
              {/* Person name with dot */}
              <div className="mb-4 flex items-center gap-2">
                <span
                  className="inline-block h-3 w-3 rounded-full"
                  style={{ backgroundColor: dotColor }}
                />
                <span className="font-heading text-[16px] font-semibold text-text-primary">
                  {person}
                </span>
              </div>

              {/* Word display area */}
              <div
                className="flex h-[220px] flex-wrap items-center justify-center gap-x-3 gap-y-2 overflow-hidden rounded-[16px] p-4"
                style={{ backgroundColor: personIdx === 0 ? "#FFF0F3" : "#F5F0FF" }}
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
                {words.length === 0 && (
                  <span className="font-body text-[14px] text-text-muted">
                    尚無資料
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Unique phrases pills */}
      {topPhrases.length > 0 && (
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <span className="font-heading text-[15px] font-semibold text-text-primary">
            專屬用語
          </span>
          {topPhrases.map((item, idx) => (
            <span
              key={item.phrase}
              className={`inline-flex items-center gap-1 rounded-full px-4 py-2 font-body text-[13px] font-medium text-text-primary ${PILL_BG_CLASSES[idx % PILL_BG_CLASSES.length]}`}
            >
              {"\u2764\uFE0F"} 「{item.phrase}」&times; {item.count} 次
            </span>
          ))}
        </div>
      )}
    </section>
  );
}
