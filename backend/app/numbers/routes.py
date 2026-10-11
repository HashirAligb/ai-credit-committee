import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models import CalcRequest, CalcResult, Company
from app.numbers.calculator import calculate

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / "data" / "cache"
router = APIRouter(prefix="/api")


def contract_cache_path(ticker: str) -> Path:
    return CACHE / f"{ticker.upper()}_contract.json"


def load_company(ticker: str) -> Company:
    path = ROOT / "data" / "companies" / f"{ticker.upper()}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Company {ticker.upper()} not found")
    config = json.loads(path.read_text())
    # Until SEC ingestion exists, the hardcoded "overrides" are the facts.
    config.setdefault("facts", config.get("overrides"))
    # If the Contract Analyst has read the real contract, its quotes and schedule replace the config's.
    cache_path = contract_cache_path(ticker)
    contract_rules = json.loads(cache_path.read_text())["rules"] if cache_path.exists() else []
    for rule in config["rules"]:
        rule.update(next((item for item in contract_rules if item["type"] == rule["type"]), {}))
        rule.setdefault("source_url", config.get("covenant_url"))
    return Company.model_validate(config)


@router.get("/company/{ticker}", response_model=Company)
def company(ticker: str) -> Company:
    return load_company(ticker)


@router.post("/calc", response_model=CalcResult)
def calc(request: CalcRequest) -> CalcResult:
    company_data = load_company(request.ticker)
    return calculate(company_data, request.earnings_drop_pct, request.refi_rate_pct)
