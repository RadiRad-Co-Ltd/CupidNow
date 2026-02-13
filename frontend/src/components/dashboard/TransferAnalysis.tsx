import { ArrowRightLeft } from "lucide-react";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

export function TransferAnalysis({ result }: Props) {
  const data = result.transferAnalysis;
  if (!data || data.totalCount === 0) return null;

  const [person1, person2] = result.persons;
  const p1Sent = data.perPerson[person1]?.sent ?? 0;
  const p2Sent = data.perPerson[person2]?.sent ?? 0;
  const p1Count = data.perPerson[person1]?.count ?? 0;
  const p2Count = data.perPerson[person2]?.count ?? 0;

  const diff = Math.abs(p1Sent - p2Sent);
  const bigSpender = p1Sent >= p2Sent ? person1 : person2;

  // Bar widths
  const maxSent = Math.max(p1Sent, p2Sent, 1);
  const p1Pct = Math.round((p1Sent / maxSent) * 100);
  const p2Pct = Math.round((p2Sent / maxSent) * 100);

  return (
    <section className="w-full bg-white px-4 py-8 sm:px-8 md:px-12 md:py-12 lg:px-20">
      <div className="flex items-center gap-2">
        <ArrowRightLeft className="h-5 w-5 text-teal-accent" />
        <h2 className="font-heading text-[20px] sm:text-[24px] font-bold text-text-primary">
          轉帳紀錄
        </h2>
      </div>
      <p className="mt-2 font-body text-[14px] text-text-secondary">
        共 {data.totalCount} 筆轉帳，合計 NT$ {data.totalAmount.toLocaleString()}
      </p>

      <div className="mt-6 rounded-[16px] sm:rounded-[20px] border border-border-light bg-white p-4 sm:p-6 md:px-10 md:py-8">
        {/* Legend */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-rose-primary" />
            <span className="font-body text-[15px] font-bold text-rose-primary">{person1}</span>
          </div>
          <span className="font-heading text-[14px] font-semibold text-text-muted">vs</span>
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-purple-accent" />
            <span className="font-body text-[15px] font-bold text-purple-accent">{person2}</span>
          </div>
        </div>

        {/* Bars */}
        <div className="flex flex-col gap-5">
          {/* Person 1 */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="font-body text-[13px] font-semibold text-text-primary">
                {person1} 轉出
              </span>
              <span className="font-body text-[12px] font-medium text-text-secondary">
                NT$ {p1Sent.toLocaleString()}（{p1Count} 筆）
              </span>
            </div>
            <div className="flex h-7 overflow-hidden rounded-full bg-rose-soft">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${p1Pct}%`,
                  background: "linear-gradient(90deg, #E8457E 0%, #F472B6 100%)",
                }}
              />
            </div>
          </div>

          {/* Person 2 */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="font-body text-[13px] font-semibold text-text-primary">
                {person2} 轉出
              </span>
              <span className="font-body text-[12px] font-medium text-text-secondary">
                NT$ {p2Sent.toLocaleString()}（{p2Count} 筆）
              </span>
            </div>
            <div className="flex h-7 overflow-hidden rounded-full bg-purple-100">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${p2Pct}%`,
                  background: "linear-gradient(90deg, #9F7AEA 0%, #B794F4 100%)",
                }}
              />
            </div>
          </div>
        </div>

        {/* Verdict */}
        <div className="mt-6 flex items-center gap-2 rounded-xl bg-gold-soft px-4 py-2.5">
          <span className="font-body text-[13px] text-text-primary">
            {diff === 0 ? (
              "兩人轉帳金額一樣多！"
            ) : (
              <><b>{bigSpender}</b> 多付了 <b>NT$ {diff.toLocaleString()}</b></>
            )}
          </span>
        </div>
      </div>
    </section>
  );
}
