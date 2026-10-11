"""Checks the pipeline's shape and the fallback without calling Gemini."""
import asyncio
import json
from app.agents import routes
from app.agents.briefing import build_briefing
from app.agents import contract
from app.agents.contract import AgentOutput, ContractExtraction, find_section, html_to_text
from app.agents.debate import ChairOutput
from app.agents.graph import run_committee
from app.models import CalcRequest
from app.numbers.calculator import calculate
from app.numbers.routes import load_company

COMPANY = load_company("PZCO")


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
    events = asyncio.run(collect(run_committee("PZCO", 0, 5)))
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


def test_silgan_briefing_uses_net_leverage_and_the_step_down():
    silgan = load_company("SLGN")
    briefing = build_briefing(silgan, calculate(silgan, 30, 10), 30, 10)
    assert "Net leverage (the ratio the loan rule tests): 5.12x" in briefing
    assert "Total debt: $4.36B" in briefing
    assert "5.25x through 2025, 5.00x in 2026, 4.75x in 2027, 4.50x from 2028 on" in briefing
    assert "2028 is also the year $1.38B of debt comes due" in briefing
    assert "2031+: $710M of debt due" in briefing
    assert "Free cash flow per year: -$99M" in briefing
    assert "Revolver unavailable: covenant breach" in briefing
    assert "First shortfall: 2028, when $1.38B comes due against $0M of liquidity, a gap of $1.38B" in briefing


def test_silgan_baseline_briefing_reports_no_shortfall():
    silgan = load_company("SLGN")
    rate = silgan.facts.interest / silgan.facts.total_debt * 100
    briefing = build_briefing(silgan, calculate(silgan, 0, rate), 0, rate)
    assert "No shortfall: liquidity covers the debt due in every year." in briefing
    assert "The $1.48B undrawn revolver is counted in liquidity." in briefing


# ---- Reading the real contract (no network: a small fake document) ----

FAKE_HTML = """<html><body><p>Section 9.07 Interest Coverage Ratio 156</p><p>Table of contents ends.</p>
<p>Section 9.07 <u>Interest Coverage Ratio</u>. None of the Borrowers will permit the ratio to be less than
<strike>2.50:1.00</strike> 3.00:1.00.</p>
<p>Section 9.08 <u>Total Net Leverage Ratio</u>. None of the Borrowers will permit the ratio to be greater than
the corresponding ratio set forth below: Period 2026 5.00:1.00 2028 and thereafter 4.50:1.00</p>
<p>Section 9.09 Limitation on Voluntary Payments. Nothing here.</p></body></html>"""


def test_html_to_text_drops_struck_out_wording_and_finds_sections():
    text = html_to_text(FAKE_HTML)
    assert "2.50" not in text
    section = find_section(text, "9.07")
    assert section.startswith("Section 9.07 Interest Coverage Ratio . None of the Borrowers")
    assert "Section 9.08" not in section and "Table of contents" not in section


def read_fake_contract(monkeypatch, tmp_path, coverage_quote):
    silgan = load_company("SLGN")
    monkeypatch.setattr(contract, "contract_cache_path", lambda ticker: tmp_path / f"{ticker}_contract.json")

    async def fake_fetch(company):
        return html_to_text(FAKE_HTML)

    async def fake_extract(role, briefing, schema):
        return ContractExtraction.model_validate({"rules": [
            {"section": "9.07", "quote": coverage_quote, "thresholds": [{"year": None, "threshold": 3.0}]},
            {"section": "9.08", "quote": "None of the Borrowers will permit the ratio to be greater than the corresponding ratio set forth below:",
             "thresholds": [{"year": 2026, "threshold": 5.0}, {"year": 2028, "threshold": 4.5}]},
        ]})

    monkeypatch.setattr(contract, "fetch_contract_text", fake_fetch)
    monkeypatch.setattr(contract, "ask", fake_extract)
    asyncio.run(contract.ensure_contract_is_read(silgan.model_copy(update={"covenant_url": "https://example.test"})))
    return tmp_path / "SLGN_contract.json"


def test_contract_read_is_cached_when_quotes_are_in_the_document(monkeypatch, tmp_path):
    cache = read_fake_contract(monkeypatch, tmp_path, "None of the Borrowers will permit the ratio to be less than 3.00:1.00.")
    rules = {rule["type"]: rule for rule in json.loads(cache.read_text())["rules"]}
    assert rules["max_net_leverage"]["threshold"] == 5.0
    assert rules["max_net_leverage"]["schedule"] == [{"year": 2026, "threshold": 5.0}, {"year": 2028, "threshold": 4.5}]
    assert rules["min_coverage"]["schedule"] == []


def test_contract_read_is_rejected_when_a_quote_is_not_verbatim(monkeypatch, tmp_path):
    cache = read_fake_contract(monkeypatch, tmp_path, "The Borrowers shall keep coverage above 3.00:1.00.")
    assert not cache.exists()  # failure is logged and the config rules stay in use
