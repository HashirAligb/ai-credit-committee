import json
import asyncio
import uuid
from pathlib import Path
from collections.abc import AsyncIterator
from fastapi.responses import StreamingResponse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import CalcRequest, Company
from app.numbers.calculator import calculate

ROOT = Path(__file__).resolve().parents[2]
app = FastAPI(title="AI Credit Committee API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
RUNS: dict[str, CalcRequest] = {}


def load_company(ticker: str) -> Company:
    path = ROOT / "data" / "companies" / f"{ticker.upper()}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Company {ticker.upper()} not found")
    return Company.model_validate(json.loads(path.read_text()))


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/company/{ticker}", response_model=Company)
def company(ticker: str) -> Company:
    return load_company(ticker)


@app.post("/api/calc")
def calc(request: CalcRequest):
    company_data = load_company(request.ticker)
    return calculate(company_data, request.earnings_drop_pct, request.refi_rate_pct)


@app.post("/api/runs")
def create_run(request: CalcRequest) -> dict[str, str]:
    run_id = str(uuid.uuid4())
    RUNS[run_id] = request
    return {"run_id": run_id}


async def run_events(run_id: str) -> AsyncIterator[str]:
    request = RUNS.get(run_id)
    if request is None:
        yield f"event: error\ndata: {json.dumps({'message': 'Run not found'})}\n\n"
        return
    company_data = load_company(request.ticker)
    result = calculate(company_data, request.earnings_drop_pct, request.refi_rate_pct)
    stressed = any(not check.passed for check in result.rule_checks)
    scenario = "stress" if stressed else "baseline"
    demo_path = ROOT / "data" / "demo_runs" / f"{company_data.ticker}_{scenario}.json"
    events = json.loads(demo_path.read_text())["events"]
    for event in events:
        await asyncio.sleep(1)
        yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"


@app.get("/api/runs/{run_id}/stream")
async def stream_run(run_id: str):
    return StreamingResponse(run_events(run_id), media_type="text/event-stream")
