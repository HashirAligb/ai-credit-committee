import asyncio
import json
import logging
import os
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.briefing import build_briefing
from app.agents.graph import run_committee
from app.models import CalcRequest, CalcResult
from app.numbers.calculator import calculate
from app.numbers.routes import ROOT, load_company

router = APIRouter(prefix="/api")
logger = logging.getLogger("uvicorn.error")
RUNS: dict[str, CalcRequest] = {}


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/runs")
def create_run(request: CalcRequest) -> dict[str, str]:
    load_company(request.ticker)  # 404 here rather than mid-stream
    run_id = str(uuid.uuid4())
    RUNS[run_id] = request
    return {"run_id": run_id}


async def replay_saved_run(ticker: str, calc: CalcResult) -> AsyncIterator[str]:
    """Demo mode and the safety net: replay a saved run with realistic delays."""
    stressed = any(not check.passed for check in calc.rule_checks)
    scenario = "stress" if stressed else "baseline"
    demo_path = ROOT / "data" / "demo_runs" / f"{ticker}_{scenario}.json"
    if not demo_path.exists():
        yield sse("error", {"message": f"No saved {scenario} run for {ticker}"})
        return
    for event in json.loads(demo_path.read_text())["events"]:
        # Agents that run in parallel start together; the pause is the "thinking" time.
        if event["type"] != "agent_started":
            await asyncio.sleep(1.2)
        yield sse(event["type"], event["data"])


async def run_events(run_id: str) -> AsyncIterator[str]:
    request = RUNS.get(run_id)
    if request is None:
        yield sse("error", {"message": "Run not found"})
        return
    company = load_company(request.ticker)
    calc = calculate(company, request.earnings_drop_pct, request.refi_rate_pct)

    if os.getenv("DEMO_MODE") != "1":
        briefing = build_briefing(company, calc, request.earnings_drop_pct, request.refi_rate_pct)
        try:
            async for event in run_committee(briefing):
                yield sse(event["type"], event["data"])
            return
        except Exception:
            # Any Gemini failure (bad key, timeout, rate limit, bad JSON): don't die on stage.
            logger.exception("Live committee failed for %s; falling back to the saved run", company.ticker)

    async for chunk in replay_saved_run(company.ticker, calc):
        yield chunk


@router.get("/runs/{run_id}/stream")
async def stream_run(run_id: str) -> StreamingResponse:
    return StreamingResponse(run_events(run_id), media_type="text/event-stream")
