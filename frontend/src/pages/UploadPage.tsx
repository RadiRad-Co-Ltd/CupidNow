import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Heart, Sparkles, ShieldCheck, Trash2, EyeOff, UserX } from "lucide-react";
import { FileDropzone } from "../components/FileDropzone";
import type { AnalysisResult } from "../types/analysis";

const API_BASE = import.meta.env.VITE_API_URL || '';

interface Props {
  onResult: (result: AnalysisResult) => void;
}

const LOADING_TEXTS = [
  "正在解讀你們的故事...",
  "計算心動的瞬間...",
  "分析互動指數...",
  "尋找最甜蜜的對話...",
];

const PRIVACY_BADGES = [
  { icon: ShieldCheck, label: "HTTPS 加密傳輸", color: "text-teal-positive" },
  { icon: Trash2, label: "分析完即銷毀", color: "text-rose-primary" },
  { icon: EyeOff, label: "純記憶體處理", color: "text-purple-accent" },
  { icon: UserX, label: "無需註冊帳號", color: "text-gold-accent" },
];

export function UploadPage({ onResult }: Props) {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleFile = async (file: File) => {
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      if (file.size > 10 * 1024 * 1024) {
        setError("檔案太大，最大限制 10MB");
        setLoading(false);
        return;
      }

      setProgress(20);

      const formData = new FormData();
      formData.append("file", file);

      const resp = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        body: formData,
      });

      setProgress(90);
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "分析失敗" }));
        throw new Error(err.detail || "分析失敗");
      }

      const result: AnalysisResult = await resp.json();
      setProgress(100);
      onResult(result);
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
          <div className="flex w-full max-w-md flex-col items-center gap-4 rounded-3xl border border-border-light bg-white p-12">
            <div className="h-2 w-full overflow-hidden rounded-full bg-rose-soft">
              <div
                className="h-full rounded-full bg-gradient-to-r from-rose-primary to-purple-accent transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="animate-pulse text-sm text-text-secondary">
              {LOADING_TEXTS[Math.floor((progress / 100) * LOADING_TEXTS.length) % LOADING_TEXTS.length]}
            </p>
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
