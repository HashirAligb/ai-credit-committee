import type { Decision, Verdict } from "../lib/api";
import { Card } from "./ui/card";

const badges: Record<Decision, { label: string; style: string }> = {
  lend: { label: "LEND", style: "bg-emerald-400/20 text-emerald-300" },
  lend_with_conditions: { label: "LEND WITH CONDITIONS", style: "bg-amber-400/20 text-amber-300" },
  dont_lend: { label: "DON’T LEND", style: "bg-red-400/20 text-red-300" },
};

export function VerdictCard({ verdict, stale, error }: { verdict: Verdict | null; stale: boolean; error: string | null }) {
  const badge = verdict ? badges[verdict.decision] ?? badges.dont_lend : null;
  return (
    <Card>
      <h2 className="mb-4 text-lg font-bold">Committee verdict</h2>
      {error && <p className="mb-4 text-sm text-red-300">{error}</p>}
      {verdict && badge ? (
        <>
          <span className={`inline-block rounded-full px-4 py-2 text-sm font-bold ${badge.style}`}>{badge.label}</span>
          <p className="mt-5 leading-7 text-slate-300">{verdict.text}</p>
          {stale && <p className="mt-4 text-sm text-amber-300">The sliders have moved since this verdict. Re-run the committee.</p>}
        </>
      ) : !error && <p className="text-slate-400">Run the committee to see the debate and the final decision.</p>}
    </Card>
  );
}
