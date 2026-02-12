import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

interface NightCard {
  emoji: string;
  value: string;
  label: string;
}

function formatHoursToTime(floatHours: number): string {
  const totalMinutes = Math.round(floatHours * 60);
  let hours = Math.floor(totalMinutes / 60) % 24;
  const minutes = totalMinutes % 60;
  const ampm = hours >= 12 ? "PM" : "AM";
  const displayHours = hours % 12 || 12;
  return `${displayHours}:${String(minutes).padStart(2, "0")} ${ampm}`;
}

function getTopPerson(record: Record<string, number>): string {
  let topPerson = "";
  let topCount = -1;
  for (const [person, count] of Object.entries(record)) {
    if (count > topCount) {
      topCount = count;
      topPerson = person;
    }
  }
  return topPerson || "—";
}

export function GoodnightAnalysis({ result }: Props) {
  const { goodnightAnalysis } = result.timePatterns;
  const { totalDays } = result.basicStats.dateRange;

  const cards: NightCard[] = [
    {
      emoji: "\uD83C\uDF19",
      value: getTopPerson(goodnightAnalysis.whoSaysGoodnightFirst),
      label: "誰先說晚安",
    },
    {
      emoji: "\u23F0",
      value: formatHoursToTime(goodnightAnalysis.avgLastChatTime),
      label: "平均最晚聊到",
    },
    {
      emoji: "\u2600\uFE0F",
      value: getTopPerson(goodnightAnalysis.whoSaysGoodmorningFirst),
      label: "誰先說早安",
    },
    {
      emoji: "\u23F1\uFE0F",
      value: String(totalDays),
      label: "聊天天數",
    },
  ];

  return (
    <section className="w-full bg-white" style={{ padding: "48px 80px" }}>
      <h2 className="mb-6 font-heading text-[24px] font-bold text-text-primary">
        晚安分析
      </h2>

      <div className="grid grid-cols-4 gap-5">
        {cards.map((card) => (
          <div
            key={card.label}
            className="flex flex-col items-center gap-4 rounded-[20px] p-7"
            style={{
              background:
                "linear-gradient(150deg, #1A1035 0%, #2D1B4E 100%)",
            }}
          >
            <span className="text-[32px]">{card.emoji}</span>
            <span className="font-heading text-[22px] font-extrabold text-white">
              {card.value}
            </span>
            <span className="font-body text-[13px] font-medium text-white/70">
              {card.label}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
