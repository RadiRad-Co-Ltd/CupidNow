import { useRef, useState, useCallback, useEffect } from "react";
import { Download, Loader2, Heart, Flame } from "lucide-react";
import { toPng } from "html-to-image";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
  reportRef: React.RefObject<HTMLElement | null>;
  onRegister?: (fn: () => Promise<void>) => void;
}

const SENTIMENT_LABELS: Record<string, string> = {
  sweet: "甜蜜", flirty: "曖昧", daily: "日常", conflict: "衝突", missing: "思念",
};

/** Capture a DOM element and return its PNG data URL. */
async function captureElement(
  element: HTMLElement,
  pixelRatio: number,
  styleOverride?: Partial<CSSStyleDeclaration>,
): Promise<string> {
  const opts: Parameters<typeof toPng>[1] = {
    pixelRatio,
    cacheBust: true,
    width: element.scrollWidth || element.offsetWidth,
    height: element.scrollHeight || element.offsetHeight,
    style: styleOverride,
  };
  // First call warms up fonts — html-to-image often returns blank on first try
  await toPng(element, opts).catch(() => {});
  // Second call captures correctly
  return toPng(element, opts);
}

/** Convert data URL to File object for Web Share API. */
function dataUrlToFile(dataUrl: string, filename: string): File {
  const [header, base64] = dataUrl.split(",");
  const mime = header.match(/:(.*?);/)?.[1] ?? "image/png";
  const bytes = atob(base64);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  return new File([arr], filename, { type: mime });
}

/** Trigger file download from data URL. */
function downloadDataUrl(dataUrl: string, filename: string) {
  const a = document.createElement("a");
  a.href = dataUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

export function ShareCTA({ result, reportRef, onRegister }: Props) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const score = result.aiAnalysis?.loveScore.score ?? 0;
  const comment = result.aiAnalysis?.loveScore.comment ?? "";
  const [p1, p2] = result.persons;
  const { totalDays } = result.basicStats.dateRange;
  const totalMessages = result.basicStats.messageCount.total ?? 0;
  const sentiment = result.aiAnalysis?.sentiment;
  const topSentiment = sentiment
    ? Object.entries(sentiment).sort((a, b) => b[1] - a[1])[0]
    : null;

  const cardStyleOverride = {
    position: "static", left: "auto", top: "auto",
  } as Partial<CSSStyleDeclaration>;

  /** Generate share card PNG and share via Web Share API (social platforms). */
  const handleShareToSocial = useCallback(async () => {
    if (!cardRef.current || generating) return;
    setGenerating(true);
    try {
      const filename = `CupidNow-${p1}&${p2}-分享卡.png`;
      const dataUrl = await captureElement(cardRef.current, 2, cardStyleOverride);
      const file = dataUrlToFile(dataUrl, filename);

      // Check if Web Share API with files is supported
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({
          title: `CupidNow — ${p1} & ${p2} 的心動報告`,
          text: `我們的心動指數是 ${score} 分！快來看看我們的聊天分析 💕`,
          files: [file],
        });
      } else {
        // Fallback: download the image if Web Share API is not available
        downloadDataUrl(dataUrl, filename);
      }
    } catch (e) {
      // User cancelled share dialog — not an error
      if (e instanceof Error && e.name === "AbortError") return;
      console.error("Share failed:", e);
    } finally {
      setGenerating(false);
    }
  }, [generating, p1, p2, score]);

  // Register the social share handler for the header button
  useEffect(() => {
    if (onRegister) onRegister(handleShareToSocial);
  }, [onRegister, handleShareToSocial]);

  /** Download share card as PNG file. */
  const handleDownloadCard = useCallback(async () => {
    if (!cardRef.current || generating) return;
    setGenerating(true);
    try {
      const dataUrl = await captureElement(cardRef.current, 2, cardStyleOverride);
      downloadDataUrl(dataUrl, `CupidNow-${p1}&${p2}-分享卡.png`);
    } catch (e) {
      console.error("Share card download failed:", e);
    } finally {
      setGenerating(false);
    }
  }, [generating, p1, p2]);

  /** Download full report as PNG file. */
  const handleDownloadReport = useCallback(async () => {
    if (downloading) return;
    const el = reportRef.current;
    if (!el) return;
    setDownloading(true);
    try {
      const dataUrl = await captureElement(el, 1);
      downloadDataUrl(dataUrl, `CupidNow-${p1}&${p2}-完整報告.png`);
    } catch (e) {
      console.error("Report download failed:", e);
      alert(`報告下載失敗: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setDownloading(false);
    }
  }, [downloading, reportRef, p1, p2]);

  const scoreLabel = score >= 80 ? "超來電！互動熱度超過 92% 的人"
    : score >= 60 ? "有感覺！互動頻率很不錯"
      : "繼續加油！";

  return (
    <>
      {/* ===== Hidden share card — always rendered off-screen ===== */}
      <div
        ref={cardRef}
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          position: "absolute",
          left: -9999,
          top: 0,
          width: 480,
          padding: "44px 36px 36px",
          background: "linear-gradient(150deg, #2D1B33 0%, #4A1942 33%, #6B2150 66%, #8B2A5E 100%)",
          borderRadius: 24,
          fontFamily: "'Plus Jakarta Sans', 'Inter', 'Noto Sans TC', sans-serif",
          boxSizing: "border-box",
        }}
      >
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 28 }}>
          <Heart size={20} color="#E8457E" fill="#E8457E" />
          <span style={{ fontSize: 18, fontWeight: 800, color: "#FFFFFF", letterSpacing: -0.5 }}>CupidNow</span>
        </div>

        {/* Label */}
        <div style={{ color: "rgba(255,255,255,0.6)", fontSize: 13, fontWeight: 500, marginBottom: 12 }}>
          心動指數
        </div>

        {/* Score */}
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 24 }}>
          <span style={{ fontSize: 72, fontWeight: 800, color: "#FFFFFF", lineHeight: 1 }}>{score}</span>
          <span style={{ fontSize: 22, fontWeight: 600, color: "rgba(255,255,255,0.4)" }}>/ 100</span>
        </div>

        {/* Badge */}
        <div style={{
          display: "flex", alignItems: "center", gap: 6,
          background: "rgba(232,69,126,0.25)", borderRadius: 100, padding: "7px 18px", marginBottom: 24,
        }}>
          <Flame size={14} color="#FF9EBF" fill="#FF9EBF" />
          <span style={{ fontSize: 12, fontWeight: 600, color: "#FFFFFF", whiteSpace: "nowrap" }}>{scoreLabel}</span>
        </div>

        {/* Comment */}
        <p style={{
          color: "rgba(255,255,255,0.65)", fontSize: 13, lineHeight: 1.7, textAlign: "center",
          maxWidth: 380, margin: "0 0 28px", padding: 0,
        }}>
          「{comment}」
        </p>

        {/* Stats */}
        <div style={{ display: "flex", gap: 10, width: "100%", marginBottom: 28 }}>
          {[
            { value: totalMessages.toLocaleString(), label: "總訊息" },
            { value: `${totalDays} 天`, label: "聊天天數" },
            { value: topSentiment ? `${SENTIMENT_LABELS[topSentiment[0]] ?? topSentiment[0]} ${topSentiment[1]}%` : "—", label: "主要情緒" },
          ].map((s) => (
            <div
              key={s.label}
              style={{
                flex: 1, display: "flex", flexDirection: "column", alignItems: "center",
                gap: 5, background: "rgba(255,255,255,0.12)", borderRadius: 14, padding: "14px 8px",
              }}
            >
              <span style={{ fontSize: 18, fontWeight: 800, color: "#FFFFFF" }}>{s.value}</span>
              <span style={{ fontSize: 10, fontWeight: 500, color: "rgba(255,255,255,0.5)" }}>{s.label}</span>
            </div>
          ))}
        </div>

        {/* Names — centered */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, width: "100%", marginBottom: 24 }}>
          <span style={{
            background: "#E8457E", color: "#FFF", fontSize: 12, fontWeight: 700,
            borderRadius: 100, padding: "6px 16px",
          }}>{p1}</span>
          <Heart size={14} color="rgba(255,255,255,0.35)" fill="rgba(255,255,255,0.35)" />
          <span style={{
            background: "#9F7AEA", color: "#FFF", fontSize: 12, fontWeight: 700,
            borderRadius: 100, padding: "6px 16px",
          }}>{p2}</span>
        </div>

        {/* Footer */}
        <div style={{ color: "rgba(255,255,255,0.25)", fontSize: 10 }}>
          cupidnow.app · Powered by AI
        </div>
      </div>

      {/* ===== Visible CTA section ===== */}
      <section
        className="flex w-full flex-col items-center"
        style={{
          background: "linear-gradient(160deg, #FFF8FA 0%, #FDF0F5 50%, #EDE4F5 100%)",
          padding: "64px 120px",
        }}
      >
        <h2 className="mb-3 text-center font-heading text-[32px] font-bold text-text-primary">
          分享你們的心動報告
        </h2>
        <p className="mb-8 text-center font-body text-[16px] text-text-secondary">
          生成一張精美的報告摘要卡，與朋友分享你們的互動數據
        </p>

        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={handleDownloadCard}
            disabled={generating}
            className="inline-flex items-center gap-2.5 rounded-full font-body text-[16px] font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            style={{
              background: "linear-gradient(135deg, #E8457E 0%, #9F7AEA 100%)",
              padding: "16px 36px",
              boxShadow: "0 6px 24px 0 #E8457E35",
            }}
          >
            {generating
              ? <><Loader2 className="h-[18px] w-[18px] animate-spin" /> 生成中...</>
              : <><Download className="h-[18px] w-[18px]" /> 下載分享卡</>}
          </button>

          <button
            type="button"
            onClick={handleDownloadReport}
            disabled={downloading}
            className="inline-flex items-center gap-2.5 rounded-full border border-border-light bg-white font-body text-[16px] font-semibold text-text-primary transition-colors hover:bg-gray-50 disabled:opacity-60"
            style={{ padding: "16px 36px" }}
          >
            {downloading
              ? <><Loader2 className="h-[18px] w-[18px] animate-spin" /> 下載中...</>
              : <><Download className="h-[18px] w-[18px]" /> 下載完整報告</>}
          </button>
        </div>
      </section>
    </>
  );
}
