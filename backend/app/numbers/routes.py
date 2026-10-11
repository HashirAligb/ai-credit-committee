import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models import CalcRequest, CalcResult, Company
from app.numbers.calculator import calculate

ROOT = Path(__file__).resolve().parents[3]
router = APIRouter(prefix="/api")


def load_company(ticker: str) -> Company:
    path = ROOT / "data" / "companies" / f"{ticker.upper()}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Company {ticker.upper()} not found")
    config = json.loads(path.read_text())
    # Until SEC ingestion exists, the hardcoded "overrides" are the facts.
    config.setdefault("facts", config.get("overrides"))
    for rule in config["rules"]:
        rule.setdefault("source_url", config.get("covenant_url"))
    return Company.model_validate(config)


@router.get("/company/{ticker}", response_model=Company)
def company(ticker: str) -> Company:
    return load_company(ticker)


@router.post("/calc", response_model=CalcResult)
def calc(request: CalcRequest) -> CalcResult:
    company_data = load_company(request.ticker)
    return calculate(company_data, request.earnings_drop_pct, request.refi_rate_pct)
