import asyncio
import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models import CalcRequest
from app.numbers.calculator import calculate
from app.numbers.routes import ROOT, load_company

router = APIRouter(prefix="/api")
RUNS: dict[str, CalcRequest] = {}


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/runs")
def create_run(request: CalcRequest) -> dict[str, str]:
    load_company(request.ticker)  # 404 here rather than mid-stream
    run_id = str(uuid.uuid4())
    RUNS[run_id] = request
    return {"run_id": run_id}


async def run_events(run_id: str) -> AsyncIterator[str]:
    """Replay a saved run. The real LangGraph committee will plug in here."""
    request = RUNS.get(run_id)
    if request is None:
        yield sse("error", {"message": "Run not found"})
        return
    company_data = load_company(request.ticker)
    result = calculate(company_data, request.earnings_drop_pct, request.refi_rate_pct)
    stressed = any(not check.passed for check in result.rule_checks)
    scenario = "stress" if stressed else "baseline"
    demo_path = ROOT / "data" / "demo_runs" / f"{company_data.ticker}_{scenario}.json"
    if not demo_path.exists():
        yield sse("error", {"message": f"No saved {scenario} run for {company_data.ticker}"})
        return
    for event in json.loads(demo_path.read_text())["events"]:
        # Agents that run in parallel start together; the pause is the "thinking" time.
        if event["type"] != "agent_started":
            await asyncio.sleep(1.2)
        yield sse(event["type"], event["data"])


@router.get("/runs/{run_id}/stream")
async def stream_run(run_id: str) -> StreamingResponse:
    return StreamingResponse(run_events(run_id), media_type="text/event-stream")
