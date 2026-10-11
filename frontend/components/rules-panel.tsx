import type { Rule, RuleCheck } from "../lib/api";
import { ratio } from "../lib/format";
import { Card } from "./ui/card";

const names: Record<Rule["type"], string> = { max_leverage: "Maximum leverage", min_coverage: "Minimum interest coverage" };

export function RulesPanel({ rules, checks, onSelect }: { rules: Rule[]; checks: RuleCheck[]; onSelect: (rule: Rule) => void }) {
  return (
    <Card>
      <h2 className="mb-1 text-lg font-bold">Loan rules</h2>
      <p className="mb-4 text-xs text-slate-400">Click a rule to see the contract sentence.</p>
      {rules.map((rule) => {
        const check = checks.find((item) => item.type === rule.type);
        const passed = check?.passed ?? false;
        return (
          <button key={rule.type} onClick={() => onSelect(rule)} className={`mb-3 flex w-full items-center justify-between rounded-xl border p-4 text-left transition hover:border-cyan-300 ${passed ? "border-slate-700" : "border-red-400/60 bg-red-400/10"}`}>
            <span>
              <span className="block font-semibold">{names[rule.type]}</span>
              <span className="text-xs text-slate-400">§{rule.section} · {rule.type === "max_leverage" ? "at most" : "at least"} {rule.threshold.toFixed(2)}x</span>
            </span>
            <span className={`font-bold ${passed ? "text-emerald-300" : "text-red-400"}`}>{passed ? "✓ PASS" : "✕ FAIL"} · {ratio(check?.value ?? null)}</span>
          </button>
        );
      })}
    </Card>
  );
}
