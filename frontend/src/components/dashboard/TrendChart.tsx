import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { AnalysisResult } from "../../types/analysis";

interface Props {
  result: AnalysisResult;
}

export function TrendChart({ result }: Props) {
  const { trend } = result.timePatterns;
  const [person1, person2] = result.persons;

  // Normalize trend data into a predictable shape
  const chartData = trend.map((entry) => ({
    period: String(entry.period ?? ""),
    [person1]: Number(entry.person1Count ?? entry[person1] ?? 0),
    [person2]: Number(entry.person2Count ?? entry[person2] ?? 0),
  }));

  // Compute a simple insight if enough data is present
  const insightText = (() => {
    if (chartData.length < 2) return null;
    const last = chartData[chartData.length - 1];
    const prev = chartData[chartData.length - 2];
    const lastTotal =
      (last[person1] as number) + (last[person2] as number);
    const prevTotal =
      (prev[person1] as number) + (prev[person2] as number);
    if (prevTotal === 0) return null;
    const change = ((lastTotal - prevTotal) / prevTotal) * 100;
    const direction = change >= 0 ? "增加" : "減少";
    return `相較前期，最近一期的訊息量${direction}了 ${Math.abs(Math.round(change))}%`;
  })();

  return (
    <div className="rounded-[20px] border border-border-light bg-white px-8 py-6">
      <h3 className="mb-5 font-heading text-base font-bold text-text-primary">
        訊息量趨勢
      </h3>

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 8, right: 8, left: -12, bottom: 0 }}
            barGap={4}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="#F3E8EE"
            />
            <XAxis
              dataKey="period"
              tick={{ fontSize: 12, fill: "#B8ADC7", fontFamily: "Inter" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#B8ADC7" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                border: "1px solid #F3E8EE",
                fontSize: 13,
                fontFamily: "Inter",
              }}
              cursor={{ fill: "#E8457E08" }}
            />
            <Legend content={() => null} />
            <Bar
              dataKey={person1}
              fill="#E8457E"
              radius={[4, 4, 0, 0]}
              maxBarSize={32}
              name={person1}
            />
            <Bar
              dataKey={person2}
              fill="#9F7AEA"
              radius={[4, 4, 0, 0]}
              maxBarSize={32}
              name={person2}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Custom legend */}
      <div className="mt-4 flex items-center justify-center gap-6">
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-rose-primary" />
          <span className="font-body text-sm text-text-secondary">
            {person1}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-purple-accent" />
          <span className="font-body text-sm text-text-secondary">
            {person2}
          </span>
        </div>
      </div>

      {/* Optional insight */}
      {insightText && (
        <div className="mt-4 rounded-[12px] bg-bg-blush px-5 py-3">
          <p className="font-body text-sm text-text-secondary">
            {insightText}
          </p>
        </div>
      )}
    </div>
  );
}
