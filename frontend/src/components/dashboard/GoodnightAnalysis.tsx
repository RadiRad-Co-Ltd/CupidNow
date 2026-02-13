import { Moon, AlarmClock, Sun, Timer, type LucideIcon } from "lucide-react";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

interface NightCard {
  icon: LucideIcon;
  iconColor: string;
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

function getTopPersonWithPercent(record: Record<string, number>): string {
  const entries = Object.entries(record);
  if (entries.length === 0) return "—";
  const total = entries.reduce((sum, [, v]) => sum + v, 0);
  if (total === 0) return "—";
  const sorted = entries.sort((a, b) => b[1] - a[1]);
  const [topPerson, topCount] = sorted[0];
  const pct = Math.round((topCount / total) * 100);
  return `${topPerson}先說 ${pct}%`;
}

export function GoodnightAnalysis({ result }: Props) {
  const { goodnightAnalysis } = result.timePatterns;
  // Estimate avg bedtime chat length (rough: time from 11pm to last chat)
  const chatMinutes = Math.max(
    Math.round((goodnightAnalysis.avgLastChatTime + 24 - 23) * 60 % (24 * 60)),
    15
  );

  const cards: NightCard[] = [
    {
      icon: Moon,
      iconColor: "#F5A623",
      value: getTopPersonWithPercent(goodnightAnalysis.whoSaysGoodnightFirst),
      label: "誰先說晚安",
    },
    {
      icon: AlarmClock,
      iconColor: "#9F7AEA",
      value: formatHoursToTime(goodnightAnalysis.avgLastChatTime),
      label: "平均最晚聊到",
    },
    {
      icon: Sun,
      iconColor: "#F472B6",
      value: getTopPersonWithPercent(goodnightAnalysis.whoSaysGoodmorningFirst),
      label: "誰先說早安",
    },
    {
      icon: Timer,
      iconColor: "#38B2AC",
      value: `${chatMinutes} 分鐘`,
      label: "平均睡前聊天時長",
    },
  ];

  return (
    <section className="w-full bg-white px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      <h2 className="mb-6 sm:mb-8 font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
        晚安分析
      </h2>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-5">
        {cards.map((card) => (
          <div
            key={card.label}
            className="flex flex-col items-center justify-center gap-3 sm:gap-4 rounded-[16px] sm:rounded-[20px] p-5 sm:p-7"
            style={{
              background:
                "linear-gradient(150deg, #1A1035 0%, #2D1B4E 100%)",
            }}
          >
            <card.icon className="h-7 w-7" style={{ color: card.iconColor }} />
            <span className="font-heading text-[18px] sm:text-[22px] font-extrabold text-white text-center">
              {card.value}
            </span>
            <span className="font-body text-[13px] font-medium text-white/70 text-center">
              {card.label}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
