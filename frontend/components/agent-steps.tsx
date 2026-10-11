import { ArrowDown, ArrowRight } from "lucide-react";
import type { Agent, AgentState, Rule } from "../lib/api";
import { Card } from "./ui/card";

const steps: { title: string; subtitle: string; agents: Agent[] }[] = [
  { title: "Step 1", subtitle: "Read the filings", agents: ["financial_analyst", "contract_analyst"] },
  { title: "Step 2", subtitle: "Debate", agents: ["bull", "bear"] },
  { title: "Step 3", subtitle: "Decide", agents: ["chair"] },
];

const labels: Record<Agent, { name: string; role: string }> = {
  financial_analyst: { name: "Financial Analyst", role: "Summarizes the numbers" },
  contract_analyst: { name: "Contract Analyst", role: "Finds the loan rules" },
  bull: { name: "Bull", role: "Argues to lend" },
  bear: { name: "Bear", role: "Argues not to lend" },
  chair: { name: "Committee Chair", role: "Writes the verdict" },
};

const statusStyles = { waiting: "text-slate-500", running: "animate-pulse text-cyan-300", done: "text-emerald-300" };
const statusLabels = { waiting: "Waiting", running: "Thinking…", done: "Done" };

type Props = { states: Partial<Record<Agent, AgentState>>; rules: Rule[]; onSelectRule: (rule: Rule) => void };

export function AgentSteps({ states, rules, onSelectRule }: Props) {
  // A source like "Credit agreement §7.11(a)" links to that rule's quote.
  const ruleFor = (source: string) => rules.find((rule) => source.includes(`§${rule.section}`));
  return (
    <Card>
      <h2 className="mb-4 text-lg font-bold">The committee</h2>
      <div className="grid items-stretch gap-3 lg:grid-cols-[1fr_auto_1fr_auto_1fr]">
        {steps.map((step, index) => (
          <div key={step.title} className="contents">
            {index > 0 && (
              <div className="flex items-center justify-center text-slate-500" aria-hidden>
                <ArrowRight className="hidden lg:block" size={28} />
                <ArrowDown className="lg:hidden" size={28} />
              </div>
            )}
            <div className="rounded-xl border border-slate-700/70 bg-slate-950/20 p-3">
              <p className="mb-3 text-xs uppercase tracking-widest text-slate-400">
                <b className="text-cyan-300">{step.title}</b> · {step.subtitle}
              </p>
              <div className="space-y-3">
                {step.agents.map((agent) => {
                  const state = states[agent] ?? { status: "waiting" };
                  return (
                    <div key={agent} className={`rounded-xl border p-4 ${state.status === "running" ? "border-cyan-300/60" : "border-slate-700"}`}>
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="text-sm font-semibold">{labels[agent].name}</span>
                        <span className={`text-xs ${statusStyles[state.status]}`}>{statusLabels[state.status]}</span>
                      </div>
                      <p className="text-xs text-slate-500">{labels[agent].role}</p>
                      {state.text && <p className="mt-3 text-sm leading-6 text-slate-200">{state.text}</p>}
                      {state.sources && state.sources.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1.5">
                          {state.sources.map((source) => {
                            const rule = ruleFor(source);
                            const chip = "rounded-full border px-2 py-0.5 text-[11px]";
                            return rule
                              ? <button key={source} onClick={() => onSelectRule(rule)} className={`${chip} border-cyan-300/50 text-cyan-300 hover:bg-cyan-300/10`}>{source}</button>
                              : <span key={source} className={`${chip} border-slate-700 text-slate-400`}>{source}</span>;
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
