import { useState, useRef, useEffect, useCallback } from "react";
import { Heart, MessageCircle, X } from "lucide-react";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit", hour12: false });
}

function formatDateLabel(iso: string): string {
  const d = new Date(iso);
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日`;
}

function dateKey(iso: string): string {
  return iso.slice(0, 10);
}

const FLOATING_HEARTS = [
  { right: 62, bottom: 8, size: 10, delay: "0s", dur: "3.2s" },
  { right: 20, bottom: 14, size: 8, delay: "0.8s", dur: "3.8s" },
  { right: 48, bottom: 4, size: 12, delay: "1.6s", dur: "4s" },
  { right: 6, bottom: 10, size: 9, delay: "2.2s", dur: "3.5s" },
];

export function FirstConversation({ result }: Props) {
  const data = result.firstConversation;
  const [open, setOpen] = useState(false);
  const [closing, setClosing] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  if (!data || data.messages.length === 0) return null;

  const persons = result.persons;
  const person1 = persons[0];

  const subtitle = data.isFallback
    ? "回顧你們最初的訊息交流"
    : `一切的開始 — ${formatDateLabel(data.startDate)}`;

  const title = data.isFallback
    ? `你們的前 ${data.messages.length} 則訊息`
    : "你們的第一次對話";

  const handleClose = useCallback(() => {
    setClosing(true);
    setTimeout(() => { setClosing(false); setOpen(false); }, 250);
  }, []);

  return (
    <div className="fixed bottom-5 right-5 z-50 sm:bottom-6 sm:right-6">
      {/* ── Floating panel ── */}
      {(open || closing) && (
        <div
          className={`absolute bottom-[72px] right-0 w-[340px] sm:w-[380px] ${closing ? "fc-panel-close" : "fc-panel-open"}`}
        >
          {/* Glow */}
          <div className="pointer-events-none absolute -inset-3 -z-10 rounded-[32px] bg-rose-primary/[0.07] blur-2xl" />

          <div className="overflow-hidden rounded-[24px] border border-rose-light/80 bg-white shadow-[0_12px_48px_-8px_rgba(232,69,126,0.22)]">
            {/* Title bar */}
            <div className="relative flex items-center justify-between border-b border-rose-light/60 bg-gradient-to-r from-rose-light/60 via-white to-purple-soft/60 px-4 py-2.5">
              <div className="flex items-center gap-2">
                <Heart className="h-3.5 w-3.5 text-rose-primary" fill="currentColor" />
                <div>
                  <span className="font-heading text-[13px] font-bold text-text-primary">
                    {title}
                  </span>
                  <p className="font-body text-[10px] leading-tight text-text-muted">{subtitle}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleClose}
                className="flex h-7 w-7 items-center justify-center rounded-full transition-colors hover:bg-rose-soft"
              >
                <X className="h-4 w-4 text-text-muted" />
              </button>
            </div>

            {/* Chat body */}
            <ChatBody
              data={data}
              person1={person1}
              chatEndRef={chatEndRef}
              open={open}
            />

            {/* Footer */}
            <div className="flex items-center justify-center gap-1.5 border-t border-rose-light/40 bg-gradient-to-r from-rose-light/30 via-white to-purple-soft/30 px-4 py-2">
              <MessageCircle className="h-3 w-3 text-rose-primary/60" />
              <span className="font-body text-[11px] text-text-muted">
                共 {data.messages.length} 則訊息
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ── FAB trigger button ── */}
      <button
        type="button"
        onClick={() => (open ? handleClose() : setOpen(true))}
        className={`relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-rose-primary to-rose-dark text-white shadow-lg transition-transform hover:scale-105 active:scale-95 ${!open ? "fc-fab-pulse" : ""}`}
      >
        {open ? (
          <X className="h-6 w-6" />
        ) : (
          <MessageCircle className="h-6 w-6" />
        )}

        {/* Floating mini hearts around FAB */}
        {!open &&
          FLOATING_HEARTS.map((h, i) => (
            <Heart
              key={i}
              className="fc-heart-float pointer-events-none absolute text-white/70"
              style={{
                right: h.right,
                bottom: h.bottom,
                width: h.size,
                height: h.size,
                animationDelay: h.delay,
                animationDuration: h.dur,
              }}
              fill="currentColor"
            />
          ))}
      </button>
    </div>
  );
}

/* Extracted so we can scroll to bottom on open */
function ChatBody({
  data,
  person1,
  chatEndRef,
  open,
}: {
  data: NonNullable<AnalysisResult["firstConversation"]>;
  person1: string;
  chatEndRef: React.RefObject<HTMLDivElement | null>;
  open: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to top when panel opens
    if (open && containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  }, [open]);

  let lastDate = "";

  return (
    <div
      ref={containerRef}
      className="overflow-y-auto bg-gradient-to-b from-bg-page to-white px-4 py-3"
      style={{ maxHeight: 380 }}
    >
      <div className="flex flex-col gap-2">
        {data.messages.map((msg, i) => {
          const msgDate = dateKey(msg.timestamp);
          const showDateSep = msgDate !== lastDate;
          lastDate = msgDate;

          const isLeft = msg.sender === person1;
          const isNonText = msg.msgType !== "text";

          return (
            <div
              key={i}
              className="fc-bubble-enter"
              style={{ animationDelay: `${0.1 + i * 0.04}s` }}
            >
              {showDateSep && (
                <div className="my-2 flex items-center justify-center">
                  <span className="fc-shimmer-bar rounded-full px-3 py-0.5 font-body text-[10px] text-text-muted">
                    {formatDateLabel(msg.timestamp)}
                  </span>
                </div>
              )}

              <div className={`flex flex-col ${isLeft ? "items-start" : "items-end"}`}>
                <span className="mb-0.5 px-1 font-body text-[10px] text-text-muted">
                  {msg.sender}
                </span>
                <div
                  className={`max-w-[80%] rounded-[16px] px-3 py-2 font-body text-[13px] leading-relaxed shadow-sm ${
                    isLeft
                      ? "rounded-tl-[4px] bg-gradient-to-br from-rose-light to-[#FFE4ED] text-text-primary"
                      : "rounded-tr-[4px] bg-gradient-to-br from-[#EDE4F7] to-purple-soft text-text-primary"
                  }`}
                >
                  {isNonText ? (
                    <span className="italic text-text-muted">{msg.content}</span>
                  ) : (
                    msg.content
                  )}
                </div>
                <span className="mt-0.5 px-1 font-body text-[10px] text-text-muted/60">
                  {formatTime(msg.timestamp)}
                </span>
              </div>
            </div>
          );
        })}
        <div ref={chatEndRef} />
      </div>
    </div>
  );
}
