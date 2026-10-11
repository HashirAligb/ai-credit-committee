"""Checks the pipeline's shape and the fallback without calling Gemini."""
import asyncio
import json
from pathlib import Path

from app.agents import routes
from app.agents.briefing import build_briefing
from app.agents.contract import AgentOutput
from app.agents.debate import ChairOutput
from app.agents.graph import run_committee
from app.models import CalcRequest, Company
from app.numbers.calculator import calculate

COMPANY = Company.model_validate(json.loads(
    (Path(__file__).parents[2] / "data/companies/PZCO.json").read_text()
))


async def fake_ask(role, briefing, schema):
    await asyncio.sleep(0.01)
    if schema is ChairOutput:
        return ChairOutput(text="Decided.", sources=["Maturity wall"], decision="lend")
    return AgentOutput(text="Said something.", sources=["What-if calculator"])


async def collect(stream):
    return [item async for item in stream]


def test_briefing_uses_calculator_numbers():
    briefing = build_briefing(COMPANY, calculate(COMPANY, 30, 10), 30, 10)
    assert "Leverage: 5.71x" in briefing
    assert "Interest coverage: 1.75x" in briefing
    assert "2 of 2 FAIL" in briefing
    assert "Credit agreement §7.11(a)" in briefing


def test_pipeline_runs_in_three_steps(monkeypatch):
    monkeypatch.setattr("app.agents.contract.ask", fake_ask)
    monkeypatch.setattr("app.agents.debate.ask", fake_ask)
    events = asyncio.run(collect(run_committee("briefing")))
    order = [(event["type"], event["data"].get("agent")) for event in events]
    # Both agents of a step start before either finishes, and steps never overlap.
    assert {agent for _, agent in order[0:2]} == {"financial_analyst", "contract_analyst"}
    assert {kind for kind, _ in order[0:2]} == {"agent_started"}
    assert {kind for kind, _ in order[2:4]} == {"agent_done"}
    assert {agent for _, agent in order[4:6]} == {"bull", "bear"}
    assert {kind for kind, _ in order[4:6]} == {"agent_started"}
    assert order[8:] == [("agent_started", "chair"), ("agent_done", "chair"), ("verdict", None)]
    assert events[-1]["data"] == {"decision": "lend", "text": "Decided."}


def test_gemini_failure_falls_back_to_saved_run(monkeypatch):
    async def broken_ask(role, briefing, schema):
        raise RuntimeError("Gemini is down")

    async def no_sleep(seconds):
        pass

    monkeypatch.setenv("DEMO_MODE", "0")
    monkeypatch.setattr("app.agents.contract.ask", broken_ask)
    monkeypatch.setattr(routes.asyncio, "sleep", no_sleep)
    routes.RUNS["test"] = CalcRequest(ticker="PZCO", earnings_drop_pct=30, refi_rate_pct=10)
    chunks = asyncio.run(collect(routes.run_events("test")))
    assert chunks[-1].startswith("event: verdict")
    assert '"decision": "dont_lend"' in chunks[-1]
