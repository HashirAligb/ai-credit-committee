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
    year: int | None  # None = "thereafter", everything due after the last listed year
    amount: float


class ScheduleStep(BaseModel):
    year: int  # the threshold applies from this year until the next step
    threshold: float


class Rule(BaseModel):
    # max_leverage = total debt / EBITDA. max_net_leverage = (total debt - cash) / EBITDA.
    type: Literal["max_leverage", "max_net_leverage", "min_coverage"]
    threshold: float
    section: str
    quote: str
    schedule: list[ScheduleStep] = []  # how the threshold changes over time, if it does
    source_url: str | None = None


class Company(BaseModel):
    ticker: str
    name: str
    fictional: bool
    fiscal_year: int
    caption: str | None = None
    covenant_url: str | None = None  # the document the loan rules are quoted from
    facts: Facts
    maturities: list[Maturity]
    rules: list[Rule]


class CalcRequest(BaseModel):
    ticker: str
    earnings_drop_pct: float = Field(ge=0, le=60)
    refi_rate_pct: float = Field(gt=0, le=15)  # 0% would make coverage infinite


class RuleCheck(BaseModel):
    type: str
    value: float | None
    threshold: float
    passed: bool


class WallPoint(BaseModel):
    year: int
    label: str  # what the chart shows: "2028", or "2031+" for the thereafter bucket
    debt_due: float
    cash_available: float  # liquidity before this year's repayment
    shortfall: float  # debt due minus liquidity, 0 if the year is covered


class CalcResult(BaseModel):
    ebitda: float
    interest: float
    fcf: float
    leverage: float | None
    net_leverage: float | None
    coverage: float
    revolver_available: bool  # False when a loan rule fails: a borrower in breach can't draw it
    rule_checks: list[RuleCheck]
    wall: list[WallPoint]
