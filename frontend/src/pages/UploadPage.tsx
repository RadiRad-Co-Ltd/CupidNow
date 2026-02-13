import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Heart, Sparkles, ShieldCheck, Trash2, EyeOff, UserX } from "lucide-react";
import { FileDropzone } from "../components/FileDropzone";
import type { AnalysisResult } from "../types/analysis";

const API_BASE = import.meta.env.VITE_API_URL || '';

interface Props {
  onResult: (result: AnalysisResult) => void;
}

const PRIVACY_BADGES = [
  { icon: ShieldCheck, label: "HTTPS 加密傳輸", color: "text-teal-positive" },
  { icon: Trash2, label: "分析完即銷毀", color: "text-rose-primary" },
  { icon: EyeOff, label: "純記憶體處理", color: "text-purple-accent" },
  { icon: UserX, label: "無需註冊帳號", color: "text-gold-accent" },
];

export function UploadPage({ onResult }: Props) {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [serverReady, setServerReady] = useState(false);
  const navigate = useNavigate();

  // Warm up backend on page load — keep polling until it responds
  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      for (let i = 0; i < 30 && !cancelled; i++) {
        try {
          const r = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(5000) });
          if (r.ok) { setServerReady(true); return; }
        } catch { /* server still waking */ }
        await new Promise((r) => setTimeout(r, 3000));
      }
    };
    poll();
    return () => { cancelled = true; };
  }, []);

  const waitForServer = async () => {
    const MAX_WAIT = 90_000; // 90 seconds max for Render cold start
    const INTERVAL = 3_000;
    const start = Date.now();
    while (Date.now() - start < MAX_WAIT) {
      try {
        const r = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(5000) });
        if (r.ok) return true;
      } catch {
        // Server still waking up
      }
      setStage(`正在喚醒伺服器...（已等 ${Math.round((Date.now() - start) / 1000)} 秒）`);
      await new Promise((r) => setTimeout(r, INTERVAL));
    }
    return false;
  };

  const handleFile = async (file: File) => {
    setLoading(true);
    setError(null);
    setProgress(2);
    setStage(serverReady ? "上傳檔案中..." : "正在喚醒伺服器，首次需要等一下...");

    try {
      if (file.size > 20 * 1024 * 1024) {
        setError("檔案太大，最大限制 20MB");
        setLoading(false);
        return;
      }

      // If server hasn't responded to warmup yet, poll until ready
      if (!serverReady) {
        const ready = await waitForServer();
        if (!ready) {
          throw new Error("伺服器喚醒逾時，請重新整理頁面再試一次");
        }
        setServerReady(true);
        setStage("上傳檔案中...");
        setProgress(3);
      }

      const formData = new FormData();
      formData.append("file", file);

      const resp = await fetch(`${API_BASE}/api/analyze-stream`, {
        method: "POST",
        body: formData,
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "分析失敗" }));
        throw new Error(err.detail || "分析失敗");
      }

      const reader = resp.body?.getReader();
      if (!reader) throw new Error("瀏覽器不支援串流");

      const decoder = new TextDecoder();
      let buffer = "";
      let finalResult: AnalysisResult | null = null;
      let aiWarning: string | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE events are separated by double newlines
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          // Collect all data: lines in this event block
          const dataLines = part
            .split("\n")
            .filter((l) => l.startsWith("data: "))
            .map((l) => l.slice(6));
          if (dataLines.length === 0) continue;
          const payload = dataLines.join("");
          try {
            const evt = JSON.parse(payload);
            if (evt.error) throw new Error(evt.error);
            if (evt.progress != null) setProgress(evt.progress);
            if (evt.stage) setStage(evt.stage);
            if (evt.warning) aiWarning = evt.warning;
            if (evt.result) finalResult = evt.result as AnalysisResult;
          } catch {
            // Incomplete or malformed event — skip
          }
        }
      }

      if (!finalResult) throw new Error("未收到分析結果");

      setProgress(100);
      setStage(aiWarning ? "完成！（AI 分析暫時不可用）" : "完成！");
      await new Promise((r) => setTimeout(r, aiWarning ? 1500 : 400));
      onResult(finalResult);
      navigate("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "發生未知錯誤");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-page">
      <header className="flex items-center justify-between px-4 sm:px-8 lg:px-20 py-4 sm:py-5">
        <div className="flex items-center gap-2">
          <Heart className="h-6 w-6 text-rose-primary" />
          <span className="font-heading text-xl font-extrabold text-text-primary">
            CupidNow
          </span>
        </div>
      </header>

      <main className="mx-auto flex max-w-2xl flex-col items-center gap-6 sm:gap-8 px-4 pt-8 sm:pt-16">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-soft px-4 py-1 text-sm font-semibold text-rose-primary">
          <Sparkles className="h-4 w-4" />
          我們重視你的隱私，請避免上傳個人敏感資訊
        </span>
        <h1 className="text-center font-heading text-3xl sm:text-4xl md:text-5xl font-extrabold leading-tight text-text-primary">
          用數據，看見心動的溫度
        </h1>
        <p className="text-center text-lg text-text-secondary">
          上傳 LINE 對話記錄，AI 幫你解讀曖昧到心動的每個瞬間
        </p>

        {loading ? (
          <div className="flex w-full max-w-md flex-col items-center gap-6 rounded-3xl border border-border-light bg-white p-10 sm:p-12">
            {/* Animated heart */}
            <div className="relative flex items-center justify-center">
              <div className="absolute h-16 w-16 animate-ping rounded-full bg-rose-primary/20" />
              <Heart className="h-10 w-10 text-rose-primary animate-pulse" fill="#E8457E" />
            </div>

            {/* Progress bar */}
            <div className="w-full">
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-rose-soft">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-rose-primary via-purple-accent to-rose-primary transition-all duration-700 ease-out"
                  style={{
                    width: `${progress}%`,
                    backgroundSize: "200% 100%",
                    animation: "shimmer 2s linear infinite",
                  }}
                />
              </div>
              <p className="mt-2 text-right font-body text-[12px] text-text-muted">
                {progress}%
              </p>
            </div>

            {/* Stage text from backend */}
            <p
              key={stage}
              className="text-center font-body text-[14px] text-text-secondary animate-fade-in"
            >
              {stage}
            </p>

            <style>{`
              @keyframes shimmer {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
              }
              @keyframes fadeIn {
                from { opacity: 0; transform: translateY(4px); }
                to { opacity: 1; transform: translateY(0); }
              }
              .animate-fade-in { animation: fadeIn 0.4s ease-out; }
            `}</style>
          </div>
        ) : (
          <FileDropzone onFileSelected={handleFile} />
        )}

        {error && (
          <p className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-600">{error}</p>
        )}

        <div className="flex flex-wrap justify-center gap-4 pt-8">
          {PRIVACY_BADGES.map((badge) => (
            <span key={badge.label} className="inline-flex items-center gap-2 rounded-full border border-border-light bg-white px-4 py-2 text-sm font-semibold text-text-primary">
              <badge.icon className={`h-4 w-4 ${badge.color}`} />
              {badge.label}
            </span>
          ))}
        </div>
      </main>
    </div>
  );
}
