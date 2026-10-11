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

    cash_available = facts.cash + facts.revolver
    wall: list[WallPoint] = []
    for maturity in sorted(company.maturities, key=lambda item: item.year):
        cash_available += stressed_fcf
        wall.append(WallPoint(year=maturity.year, debt_due=maturity.amount, cash_available=cash_available))

    return CalcResult(ebitda=stressed_ebitda, interest=stressed_interest, fcf=stressed_fcf,
                      leverage=leverage, coverage=coverage, rule_checks=checks, wall=wall)
