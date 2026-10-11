"""Builds the block of facts every agent sees, so the debate matches the dashboard."""
from app.models import CalcResult, Company


def money(amount: float) -> str:
    return f"${amount / 1e6:,.0f}M"


def ratio(value: float | None) -> str:
    return "not meaningful (EBITDA is zero or negative)" if value is None else f"{value:.2f}x"


def build_briefing(company: Company, calc: CalcResult, earnings_drop_pct: float, refi_rate_pct: float) -> str:
    facts = company.facts
    names = {"max_leverage": "Maximum leverage (total debt / EBITDA)", "min_coverage": "Minimum interest coverage (EBITDA / interest)"}
    limits = {"max_leverage": "at most", "min_coverage": "at least"}
    checks = {check.type: check for check in calc.rule_checks}

    rule_lines = []
    for rule in company.rules:
        check = checks[rule.type]
        rule_lines.append(
            f"- {names[rule.type]}, credit agreement §{rule.section}: must be {limits[rule.type]} "
            f"{rule.threshold:.2f}x. Value in this scenario: {ratio(check.value)}. "
            f"Result: {'PASS' if check.passed else 'FAIL'}.\n  Contract sentence: \"{rule.quote}\""
        )
    wall_lines = [
        f"- {point.year}: {money(point.debt_due)} of debt due, {money(point.cash_available)} of cash available"
        + (f" (short by {money(point.debt_due - point.cash_available)}, must be refinanced)" if point.debt_due > point.cash_available else "")
        for point in calc.wall
    ]
    sources = ["10-K income statement", "10-K cash flow statement", "10-K balance sheet", "10-K debt footnote",
               "What-if calculator", "Maturity wall"] + [f"Credit agreement §{rule.section}" for rule in company.rules]
    failed = sum(not check.passed for check in calc.rule_checks)

    return f"""BRIEFING: {company.name} ({company.ticker}), fiscal year {company.fiscal_year}

Reported numbers (from the 10-K):
- Cash: {money(facts.cash)}
- Total debt: {money(facts.total_debt)}
- Undrawn revolver: {money(facts.revolver)}
- EBITDA: {money(facts.ebitda)}
- Interest expense: {money(facts.interest)}
- Operating cash flow: {money(facts.ocf)}, capex: {money(facts.capex)}, free cash flow: {money(facts.ocf - facts.capex)}

Scenario being judged: earnings decline of {earnings_drop_pct:g}%, debt refinanced at {refi_rate_pct:g}%.

Numbers in this scenario (from the what-if calculator, these are the ones to judge):
- EBITDA: {money(calc.ebitda)}
- Annual interest: {money(calc.interest)}
- Free cash flow per year: {money(calc.fcf)}
- Leverage: {ratio(calc.leverage)}
- Interest coverage: {ratio(calc.coverage)}

Loan rules (covenants): {failed} of {len(calc.rule_checks)} FAIL in this scenario.
{chr(10).join(rule_lines)}

Maturity wall (cash available = cash + cumulative free cash flow + revolver):
{chr(10).join(wall_lines)}

Allowed source labels:
{chr(10).join('- ' + label for label in sources)}"""
