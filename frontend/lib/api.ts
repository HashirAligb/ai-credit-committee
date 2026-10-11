// All backend calls live here. Types mirror the API contract in CLAUDE.md.
export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Rule = { type: "max_leverage" | "min_coverage"; threshold: number; section: string; quote: string };

export type Company = {
  ticker: string; name: string; fictional: boolean; fiscal_year: number;
  facts: { cash: number; ocf: number; capex: number; ebitda: number; interest: number; total_debt: number; revolver: number };
  maturities: { year: number; amount: number }[];
  rules: Rule[];
};

export type RuleCheck = { type: string; value: number | null; threshold: number; passed: boolean };

export type CalcResult = {
  ebitda: number; interest: number; fcf: number; leverage: number | null; coverage: number;
  rule_checks: RuleCheck[];
  wall: { year: number; debt_due: number; cash_available: number }[];
};

export type Agent = "financial_analyst" | "contract_analyst" | "bull" | "bear" | "chair";
export type AgentState = { status: "waiting" | "running" | "done"; text?: string; sources?: string[] };
export type Decision = "lend" | "dont_lend" | "lend_with_conditions";
export type Verdict = { decision: Decision; text: string };

async function request<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API}${path}`, body === undefined ? undefined : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.json().then((data) => data.detail, () => null);
    throw new Error(typeof detail === "string" ? detail : `Request failed (${response.status})`);
  }
  return response.json();
}

export const getCompany = (ticker: string) => request<Company>(`/api/company/${ticker}`);

export const calculate = (ticker: string, earnings_drop_pct: number, refi_rate_pct: number) =>
  request<CalcResult>("/api/calc", { ticker, earnings_drop_pct, refi_rate_pct });

export const createRun = (ticker: string, earnings_drop_pct: number, refi_rate_pct: number) =>
  request<{ run_id: string }>("/api/runs", { ticker, earnings_drop_pct, refi_rate_pct });

export type RunHandlers = {
  onAgentStarted: (agent: Agent) => void;
  onAgentDone: (agent: Agent, text: string, sources: string[]) => void;
  onVerdict: (verdict: Verdict) => void;
  onError: (message: string) => void;
};

// Opens the SSE stream for a run. Returns a function that closes it.
export function streamRun(runId: string, handlers: RunHandlers): () => void {
  const source = new EventSource(`${API}/api/runs/${runId}/stream`);
  const data = (event: Event) => JSON.parse((event as MessageEvent).data);
  source.addEventListener("agent_started", (event) => handlers.onAgentStarted(data(event).agent));
  source.addEventListener("agent_done", (event) => {
    const { agent, text, sources } = data(event);
    handlers.onAgentDone(agent, text, sources ?? []);
  });
  source.addEventListener("verdict", (event) => { source.close(); handlers.onVerdict(data(event)); });
  // "error" fires both for our own error event (has data) and for a dropped connection (no data).
  source.addEventListener("error", (event) => {
    source.close();
    const raw = (event as MessageEvent).data;
    handlers.onError(raw ? JSON.parse(raw).message : "Lost connection to the committee.");
  });
  return () => source.close();
}
