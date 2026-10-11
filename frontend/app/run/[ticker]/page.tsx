"use client";
import { use, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Agent, calculate, CalcResult, Company, createRun, getCompany, Rule, streamRun, Verdict } from "../../../lib/api";
import { Button } from "../../../components/ui/button";
import { Card } from "../../../components/ui/card";
import { KpiCards } from "../../../components/kpi-cards";
import { MaturityWall } from "../../../components/maturity-wall";
import { RulesPanel } from "../../../components/rules-panel";
import { Sliders } from "../../../components/sliders";
import { SourceDrawer } from "../../../components/source-drawer";
import { VerdictCard } from "../../../components/verdict-card";

export type AgentState = { status: "waiting" | "running" | "done"; text?: string; sources?: string[] };
type Scenario = { drop: number; rate: number };

const agents: Agent[] = ["financial_analyst", "contract_analyst", "bull", "bear", "chair"];
const labels: Record<Agent, string> = { financial_analyst: "Financial Analyst", contract_analyst: "Contract Analyst", bull: "Bull", bear: "Bear", chair: "Committee Chair" };

export default function RunPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = use(params);
  const router = useRouter();
  const [company, setCompany] = useState<Company | null>(null);
  const [result, setResult] = useState<CalcResult | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [drop, setDrop] = useState(0);
  const [rate, setRate] = useState<number | null>(null);
  const [agentStates, setAgentStates] = useState<Partial<Record<Agent, AgentState>>>({});
  const [verdict, setVerdict] = useState<Verdict | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [ranWith, setRanWith] = useState<Scenario | null>(null);
  const [openRule, setOpenRule] = useState<Rule | null>(null);
  const closeStream = useRef<(() => void) | null>(null);

  // Load the company, and start the refi slider at its current rate so the baseline matches reported numbers.
  useEffect(() => {
    getCompany(ticker).then((data) => {
      setCompany(data);
      const currentRate = (data.facts.interest / data.facts.total_debt) * 100;
      setRate(Math.min(15, Math.max(0.5, Math.round(currentRate * 10) / 10)));
    }).catch((error: Error) => setLoadError(error.message));
    return () => closeStream.current?.();
  }, [ticker]);

  // Recalculate when a slider moves. No LLM involved, so this is instant.
  useEffect(() => {
    if (rate === null) return;
    const timer = setTimeout(() => calculate(ticker, drop, rate).then(setResult).catch((error: Error) => setLoadError(error.message)), 100);
    return () => clearTimeout(timer);
  }, [ticker, drop, rate]);

  const run = async () => {
    if (rate === null) return;
    closeStream.current?.();
    setAgentStates({}); setVerdict(null); setRunError(null); setRunning(true); setRanWith({ drop, rate });
    const fail = (message: string) => { setRunError(message); setRunning(false); };
    try {
      const { run_id } = await createRun(ticker, drop, rate);
      closeStream.current = streamRun(run_id, {
        onAgentStarted: (agent) => setAgentStates((s) => ({ ...s, [agent]: { status: "running" } })),
        onAgentDone: (agent, text, sources) => setAgentStates((s) => ({ ...s, [agent]: { status: "done", text, sources } })),
        onVerdict: (data) => { setVerdict(data); setRunning(false); },
        onError: fail,
      });
    } catch (error) {
      fail((error as Error).message);
    }
  };

  if (loadError) return <main className="p-10"><p className="text-red-300">{loadError}</p><button onClick={() => router.push("/")} className="mt-4 text-sm text-cyan-300">← Try another ticker</button></main>;
  if (!company || !result || rate === null) return <main className="p-10 text-slate-300">Loading committee workspace…</main>;

  const stale = ranWith !== null && (ranWith.drop !== drop || ranWith.rate !== rate);
  return (
    <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
      <header className="flex items-start justify-between">
        <div>
          <button onClick={() => router.push("/")} className="mb-4 text-sm text-cyan-300">← New borrower</button>
          <h1 className="text-4xl font-black">{company.name} <span className="text-lg font-normal text-slate-400">({company.ticker})</span></h1>
          <p className="mt-2 text-sm text-slate-400">{company.fictional && <span className="text-amber-300">Fictional demo company · </span>}FY {company.fiscal_year}</p>
        </div>
        <Button onClick={run} disabled={running}>{running ? "Committee in session…" : ranWith ? "Re-run committee" : "Run committee"}</Button>
      </header>

      <Card>
        <div className="grid gap-3 md:grid-cols-5">
          {agents.map((agent) => {
            const state = agentStates[agent] ?? { status: "waiting" };
            return (
              <div key={agent} className="rounded-xl border border-slate-700 p-4">
                <div className="flex justify-between">
                  <span className="text-sm font-semibold">{labels[agent]}</span>
                  <span className={`text-xs ${state.status === "done" ? "text-emerald-300" : state.status === "running" ? "text-cyan-300" : "text-slate-500"}`}>{state.status}</span>
                </div>
                <p className="mt-3 min-h-12 text-xs leading-5 text-slate-400">{state.text ?? "Awaiting turn…"}</p>
              </div>
            );
          })}
        </div>
      </Card>

      <KpiCards company={company} result={result} />

      <div className="grid gap-6 lg:grid-cols-3">
        <MaturityWall wall={result.wall} />
        <Sliders drop={drop} rate={rate} onDrop={setDrop} onRate={setRate} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <RulesPanel rules={company.rules} checks={result.rule_checks} onSelect={setOpenRule} />
        <VerdictCard verdict={verdict} stale={stale} error={runError} />
      </div>

      <SourceDrawer rule={openRule} onClose={() => setOpenRule(null)} />
    </main>
  );
}
