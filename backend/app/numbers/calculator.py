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
    net_leverage = (facts.total_debt - facts.cash) / stressed_ebitda if stressed_ebitda > 0 else None
    coverage = stressed_ebitda / stressed_interest

    checks: list[RuleCheck] = []
    for rule in company.rules:
        if rule.type == "min_coverage":
            value, passed = coverage, coverage >= rule.threshold
        else:
            value = net_leverage if rule.type == "max_net_leverage" else leverage
            passed = value is not None and value <= rule.threshold
        checks.append(RuleCheck(type=rule.type, value=value, threshold=rule.threshold, passed=passed))

    # Running liquidity, one point per year from next fiscal year through the last maturity.
    # A borrower in breach of a loan rule can't draw its revolver, so it only counts when all rules pass.
    revolver_available = all(check.passed for check in checks)
    first_year = company.fiscal_year + 1
    due_by_year: dict[int, float] = {}
    for maturity in company.maturities:
        if maturity.year is not None:
            due_by_year[maturity.year] = due_by_year.get(maturity.year, 0) + maturity.amount
    last_year = max(due_by_year, default=first_year + 4)
    labels = {year: str(year) for year in range(first_year, last_year + 1)}
    # Debt with no year ("thereafter") goes in one bucket after the last year, e.g. "2031+".
    thereafter = sum(maturity.amount for maturity in company.maturities if maturity.year is None)
    if thereafter:
        due_by_year[last_year + 1] = thereafter
        labels[last_year + 1] = f"{last_year + 1}+"
    liquidity = facts.cash + (facts.revolver if revolver_available else 0)
    wall: list[WallPoint] = []
    for year, label in labels.items():
        debt_due = due_by_year.get(year, 0)
        # Add the year's FCF, then repay the year's debt from what is there (no refinancing).
        # Liquidity can't go below zero: once it runs out, every unpaid dollar is a shortfall.
        before_repayment = max(0, liquidity + stressed_fcf)
        shortfall = max(0, debt_due - before_repayment)
        wall.append(WallPoint(year=year, label=label, debt_due=debt_due, cash_available=before_repayment, shortfall=shortfall))
        liquidity = max(0, before_repayment - debt_due)

    return CalcResult(ebitda=stressed_ebitda, interest=stressed_interest, fcf=stressed_fcf,
                      leverage=leverage, net_leverage=net_leverage, coverage=coverage,
                      revolver_available=revolver_available, rule_checks=checks, wall=wall)
