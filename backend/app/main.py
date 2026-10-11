import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import CalcRequest, Company
from app.numbers.calculator import calculate

ROOT = Path(__file__).resolve().parents[2]
app = FastAPI(title="AI Credit Committee API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


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
