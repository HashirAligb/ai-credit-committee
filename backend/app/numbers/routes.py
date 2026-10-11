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
    return Company.model_validate(json.loads(path.read_text()))


@router.get("/company/{ticker}", response_model=Company)
def company(ticker: str) -> Company:
    return load_company(ticker)


@router.post("/calc", response_model=CalcResult)
def calc(request: CalcRequest) -> CalcResult:
    company_data = load_company(request.ticker)
    return calculate(company_data, request.earnings_drop_pct, request.refi_rate_pct)
