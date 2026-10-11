import { Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CalcResult } from "../lib/api";
import { money } from "../lib/format";
import { Card } from "./ui/card";

// Both colors checked for contrast and colorblind separation on the panel background.
const DEBT_COLOR = "#e5484d";
const CASH_COLOR = "#0ea5c4";
const AXIS_COLOR = "#91a1b8";

export function MaturityWall({ wall }: { wall: CalcResult["wall"] }) {
  const short = wall.filter((point) => point.debt_due > point.cash_available);
  return (
    <Card className="lg:col-span-2">
      <h2 className="text-lg font-bold">Maturity wall</h2>
      <p className="mb-4 text-xs text-slate-400">
        Debt coming due each year against the cash on hand to pay it (cash + cumulative free cash flow + revolver).
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={wall} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
          <CartesianGrid stroke="#1c3049" vertical={false} />
          <XAxis dataKey="year" stroke={AXIS_COLOR} tickLine={false} />
          <YAxis tickFormatter={money} stroke={AXIS_COLOR} tickLine={false} axisLine={false} width={64} />
          <Tooltip
            formatter={(value: number) => money(value)}
            cursor={{ fill: "#ffffff", fillOpacity: 0.05 }}
            contentStyle={{ background: "#071426", border: "1px solid #1c3049", borderRadius: 8 }}
            labelStyle={{ color: "#f7fafc", fontWeight: 700 }}
            itemStyle={{ color: "#f7fafc" }}
          />
          <Legend verticalAlign="top" align="right" height={32} formatter={(name) => <span className="text-sm text-slate-300">{name}</span>} />
          <Bar dataKey="debt_due" name="Debt due" fill={DEBT_COLOR} maxBarSize={60} radius={[4, 4, 0, 0]} legendType="square" isAnimationActive={false} />
          <Line dataKey="cash_available" name="Cash available" type="linear" stroke={CASH_COLOR} strokeWidth={2}
            dot={{ r: 4, fill: CASH_COLOR, stroke: "#0d2037", strokeWidth: 2 }} legendType="plainline" isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
      <p className="mt-3 text-sm text-slate-300">
        {short.length === 0
          ? "Cash on hand covers the debt due in every year."
          : short.map((point) => `${point.year}: ${money(point.debt_due)} due vs ${money(point.cash_available)} of cash, a ${money(point.debt_due - point.cash_available)} gap to refinance.`).join(" ")}
      </p>
    </Card>
  );
}
