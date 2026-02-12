import { Flame, Sparkles } from "lucide-react";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

export function LoveScoreHero({ result }: Props) {
  const ai = result.aiAnalysis;
  const score = ai?.loveScore.score;
  const comment = ai?.loveScore.comment;

  return (
    <section
      className="flex w-full flex-col items-center"
      style={{
        background: "linear-gradient(150deg, #2D1B33 0%, #4A1942 33%, #6B2150 66%, #8B2A5E 100%)",
        padding: "60px 80px",
      }}
    >
      {/* Label */}
      <span
        className="font-body text-[16px] font-medium"
        style={{ color: "rgba(255, 255, 255, 0.7)" }}
      >
        你們的心動指數
      </span>

      {/* Score */}
      <div className="mt-4 flex items-baseline gap-2">
        <span className="font-heading text-[120px] font-extrabold leading-none text-white">
          {score ?? "\u2014"}
        </span>
        <span
          className="font-heading text-[32px] font-semibold"
          style={{ color: "rgba(255, 255, 255, 0.5)" }}
        >
          / 100
        </span>
      </div>

      {/* Badge */}
      <div
        className="mt-6 flex items-center gap-2 rounded-full"
        style={{
          background: "#E8457E40",
          padding: "10px 24px",
        }}
      >
        <Flame className="h-5 w-5" style={{ color: "#FF9EBF" }} />
        <span className="font-body text-[14px] font-semibold text-white">
          {!ai
            ? "等待 AI 分析中..."
            : score !== undefined && score >= 80
              ? "超來電！互動熱度超過 92% 的人"
              : score !== undefined && score >= 60
                ? "有感覺！互動頻率很不錯"
                : score !== undefined && score >= 40
                  ? "還在觀察中，繼續加油！"
                  : "互動偏少，要多聊聊喔！"}
        </span>
      </div>

      {/* AI Comment */}
      <p
        className="mt-8 max-w-[700px] text-center font-body text-[16px] leading-[1.6]"
        style={{ color: "rgba(255, 255, 255, 0.7)" }}
      >
        {comment ?? "AI 分析尚未完成，請稍候片刻，我們正在解讀你們的故事。"}
      </p>

      {/* AI Insight tag */}
      <div className="mt-8 flex items-center gap-1">
        <Sparkles className="h-3 w-3" style={{ color: "#9F7AEA" }} />
        <span className="font-body text-[12px] font-medium text-purple-accent">
          AI 洞察分析
        </span>
      </div>
    </section>
  );
}
