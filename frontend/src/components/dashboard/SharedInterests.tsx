import { MapPin, UtensilsCrossed, Film, Music, Users, type LucideIcon } from "lucide-react";
import type { AnalysisResult, SharedInterestItem } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

const ICON_MAP: Record<string, { icon: LucideIcon; color: string; bg: string }> = {
  "愛去的地方": { icon: MapPin, color: "text-rose-primary", bg: "bg-rose-soft" },
  "愛吃的東西": { icon: UtensilsCrossed, color: "text-gold-accent", bg: "bg-[#F5A62315]" },
  "愛看的劇": { icon: Film, color: "text-purple-accent", bg: "bg-purple-soft" },
  "愛看的電影": { icon: Film, color: "text-purple-accent", bg: "bg-purple-soft" },
  "愛聽的音樂": { icon: Music, color: "text-teal-positive", bg: "bg-[#38B2AC15]" },
  "常一起做的事": { icon: Users, color: "text-rose-primary", bg: "bg-rose-soft" },
};

const FALLBACK_STYLE = { icon: Users, color: "text-purple-accent", bg: "bg-purple-soft" };

function getStyle(category: string) {
  for (const [key, style] of Object.entries(ICON_MAP)) {
    if (category.includes(key) || key.includes(category)) return style;
  }
  return FALLBACK_STYLE;
}

function normalizeItem(item: string | SharedInterestItem): { name: string; count?: number } {
  if (typeof item === "string") return { name: item };
  return { name: item.name, count: item.count };
}

export function SharedInterests({ result }: Props) {
  const interests = result.textAnalysis?.sharedInterests;
  if (!interests || interests.length === 0) return null;

  return (
    <section className="w-full bg-white px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      <h2 className="mb-6 sm:mb-8 font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
        你們的共同小宇宙
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        {interests.map((interest) => {
          const style = getStyle(interest.category);
          const IconComp = style.icon;
          const items = interest.items.map(normalizeItem);
          return (
            <div
              key={interest.category}
              className="flex flex-col gap-3 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-5 sm:p-7"
            >
              <div className="flex items-center gap-2">
                <span className={`inline-flex items-center justify-center h-8 w-8 rounded-full ${style.bg}`}>
                  <IconComp className={`h-4 w-4 ${style.color}`} />
                </span>
                <span className="font-heading text-[15px] font-bold text-text-primary">
                  {interest.category}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {items.map((item) => (
                  <span
                    key={item.name}
                    className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 font-body text-[13px] font-medium ${style.bg} ${style.color}`}
                  >
                    {item.name}
                    {item.count != null && (
                      <span className="opacity-60 text-[11px]">{item.count}次</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
