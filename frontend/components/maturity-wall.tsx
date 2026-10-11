import { Bar, CartesianGrid, ComposedChart, LabelList, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CalcResult } from "../lib/api";
import { money } from "../lib/format";
import { Card } from "./ui/card";

// Both colors checked for contrast and colorblind separation on the panel background.
const DEBT_COLOR = "#e5484d";
const CASH_COLOR = "#0ea5c4";
const AXIS_COLOR = "#91a1b8";
const SHORTFALL_COLOR = "#fca5a5";

type Wall = CalcResult["wall"];
type LabelProps = { x?: number | string; y?: number | string; width?: number | string; index?: number };

export function MaturityWall({ wall, revolverAvailable, hasRevolver }: { wall: Wall; revolverAvailable: boolean; hasRevolver: boolean }) {
  const short = wall.filter((point) => point.shortfall > 0);

  // Red label above the bar in any year the debt due is more than the liquidity on hand.
  const shortfallLabel = ({ x, y, width, index }: LabelProps) => {
    const point = index === undefined ? undefined : wall[index];
    if (!point || point.shortfall <= 0) return null;
    const center = Number(x) + Number(width) / 2;
    return (
      <text x={center} y={Number(y) - 8} textAnchor="middle" fill={SHORTFALL_COLOR} fontSize={11} fontWeight={700}>
        <tspan x={center} dy="-1.1em">SHORTFALL</tspan>
        <tspan x={center} dy="1.1em">{money(point.shortfall)}</tspan>
      </text>
    );
  };

  return (
    <Card className="lg:col-span-2">
      <h2 className="text-lg font-bold">Maturity wall</h2>
      <p className="text-xs text-slate-400">
        Debt due each year against the liquidity left to repay it: cash + revolver, plus each year&apos;s free cash flow,
        minus debt already repaid. No refinancing assumed.
      </p>
      {hasRevolver && !revolverAvailable && (
        <p className="mt-2 inline-block rounded-full bg-red-400/15 px-3 py-1 text-xs font-semibold text-red-300">
          ⚠ Revolver unavailable: covenant breach
        </p>
      )}
      <div className="mt-3">
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={wall} margin={{ top: 34, right: 16, bottom: 0, left: 8 }}>
            <CartesianGrid stroke="#1c3049" vertical={false} />
            <XAxis dataKey="label" stroke={AXIS_COLOR} tickLine={false} />
            <YAxis tickFormatter={money} stroke={AXIS_COLOR} tickLine={false} axisLine={false} width={72} />
            <Tooltip
              formatter={(value: number) => money(value)}
              cursor={{ fill: "#ffffff", fillOpacity: 0.05 }}
              contentStyle={{ background: "#071426", border: "1px solid #1c3049", borderRadius: 8 }}
              labelStyle={{ color: "#f7fafc", fontWeight: 700 }}
              itemStyle={{ color: "#f7fafc" }}
            />
            <Legend verticalAlign="top" align="right" height={32} wrapperStyle={{ top: 0 }} formatter={(name) => <span className="text-sm text-slate-300">{name}</span>} />
            <Bar dataKey="debt_due" name="Debt due" fill={DEBT_COLOR} maxBarSize={60} radius={[4, 4, 0, 0]} legendType="square" isAnimationActive={false}>
              <LabelList content={shortfallLabel} />
            </Bar>
            <Line dataKey="cash_available" name="Liquidity before repayment" type="linear" stroke={CASH_COLOR} strokeWidth={2}
              dot={{ r: 4, fill: CASH_COLOR, stroke: "#0d2037", strokeWidth: 2 }} legendType="plainline" isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-sm text-slate-300">
        {short.length === 0
          ? "Liquidity covers the debt due in every year."
          : `First shortfall in ${short[0].label}: ${money(short[0].debt_due)} due against ${money(short[0].cash_available)} of liquidity, a ${money(short[0].shortfall)} gap that would have to be refinanced.`}
      </p>
    </Card>
  );
}
