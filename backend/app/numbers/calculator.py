from app.models import CalcResult, Company, RuleCheck, WallPoint


def calculate(company: Company, earnings_drop_pct: float, refi_rate_pct: float) -> CalcResult:
    facts = company.facts
    drop = earnings_drop_pct / 100
    fcf = facts.ocf - facts.capex
    ebitda = facts.ebitda
    interest = facts.interest
    stressed_ebitda = ebitda * (1 - drop)
    stressed_interest = facts.total_debt * refi_rate_pct / 100
    stressed_fcf = fcf - ebitda * drop - (stressed_interest - interest)
    leverage = facts.total_debt / stressed_ebitda if stressed_ebitda > 0 else None
    coverage = stressed_ebitda / stressed_interest

    checks: list[RuleCheck] = []
    for rule in company.rules:
        if rule.type == "max_leverage":
            checks.append(RuleCheck(type=rule.type, value=leverage, threshold=rule.threshold,
                                    passed=leverage is not None and leverage <= rule.threshold))
        else:
            checks.append(RuleCheck(type=rule.type, value=coverage, threshold=rule.threshold,
                                    passed=coverage >= rule.threshold))

    # One point per year from next fiscal year through the last maturity, so the
    # chart has no gaps. Cash builds by one year of stressed FCF each year.
    due_by_year: dict[int, float] = {}
    for maturity in company.maturities:
        due_by_year[maturity.year] = due_by_year.get(maturity.year, 0) + maturity.amount
    first_year = company.fiscal_year + 1
    last_year = max(due_by_year, default=first_year + 4)
    wall: list[WallPoint] = []
    for year in range(first_year, last_year + 1):
        years_out = year - company.fiscal_year
        cash_available = facts.cash + stressed_fcf * years_out + facts.revolver
        wall.append(WallPoint(year=year, debt_due=due_by_year.get(year, 0), cash_available=cash_available))

    return CalcResult(ebitda=stressed_ebitda, interest=stressed_interest, fcf=stressed_fcf,
                      leverage=leverage, coverage=coverage, rule_checks=checks, wall=wall)
