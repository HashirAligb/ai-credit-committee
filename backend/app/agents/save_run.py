"""Run the live committee once and save it as a demo run for DEMO_MODE.

    cd backend && python -m app.agents.save_run SLGN 0 current     (baseline at the company's own rate)
    cd backend && python -m app.agents.save_run SLGN 30 10         (stress)

The file is named <TICKER>_baseline.json if every loan rule passes, <TICKER>_stress.json if any fails.
"""
import asyncio
import json
import sys

import app.main  # noqa: F401  (loads .env)
from app.agents.graph import run_committee
from app.numbers.calculator import calculate
from app.numbers.routes import ROOT, load_company


async def main(ticker: str, drop: float, rate_arg: str) -> None:
    company = load_company(ticker)
    rate = company.facts.interest / company.facts.total_debt * 100 if rate_arg == "current" else float(rate_arg)
    calc = calculate(company, drop, rate)
    scenario = "stress" if any(not check.passed for check in calc.rule_checks) else "baseline"

    events = []
    async for event in run_committee(company.ticker, drop, rate):  # raises if Gemini fails, so nothing half-done is saved
        events.append(event)
        if event["type"] == "agent_done":
            print(f"\n{event['data']['agent'].upper()}: {event['data']['text']}\n  sources: {event['data']['sources']}")
        elif event["type"] == "verdict":
            print(f"\nVERDICT: {event['data']['decision']}")

    path = ROOT / "data" / "demo_runs" / f"{company.ticker}_{scenario}.json"
    saved = {"ticker": company.ticker, "earnings_drop_pct": drop, "refi_rate_pct": round(rate, 2), "events": events}
    path.write_text(json.dumps(saved, indent=1, ensure_ascii=False) + "\n")
    print(f"\nSaved {len(events)} events to {path.relative_to(ROOT)}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], float(sys.argv[2]), sys.argv[3]))
