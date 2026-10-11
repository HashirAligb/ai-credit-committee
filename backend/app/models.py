from typing import Literal

from pydantic import BaseModel, Field


class Facts(BaseModel):
    cash: float
    ocf: float
    capex: float
    ebitda: float
    interest: float
    total_debt: float
    revolver: float


class Maturity(BaseModel):
    year: int
    amount: float


class Rule(BaseModel):
    type: Literal["max_leverage", "min_coverage"]
    threshold: float
    section: str
    quote: str


class Company(BaseModel):
    ticker: str
    name: str
    fictional: bool
    fiscal_year: int
    facts: Facts
    maturities: list[Maturity]
    rules: list[Rule]


class CalcRequest(BaseModel):
    ticker: str
    earnings_drop_pct: float = Field(ge=0, le=60)
    refi_rate_pct: float = Field(ge=0, le=15)


class RuleCheck(BaseModel):
    type: str
    value: float | None
    threshold: float
    passed: bool


class WallPoint(BaseModel):
    year: int
    debt_due: float
    cash_available: float


class CalcResult(BaseModel):
    ebitda: float
    interest: float
    fcf: float
    leverage: float | None
    coverage: float
    rule_checks: list[RuleCheck]
    wall: list[WallPoint]
