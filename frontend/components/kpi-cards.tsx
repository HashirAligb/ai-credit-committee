import type { CalcResult, Company } from "../lib/api";
import { money, ratio } from "../lib/format";
import { Card } from "./ui/card";

export function KpiCards({ company, result }: { company: Company; result: CalcResult }) {
  const kpis = [
    ["Cash", money(company.facts.cash)],
    ["Total debt", money(company.facts.total_debt)],
    ["Free cash flow", money(result.fcf)],
    ["Leverage", ratio(result.leverage)],
    ["Interest coverage", ratio(result.coverage)],
  ];
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
      {kpis.map(([name, value]) => (
        <Card key={name}>
          <p className="text-sm text-slate-400">{name}</p>
          <p className="mt-2 text-2xl font-black">{value}</p>
        </Card>
      ))}
    </div>
  );
}
