"""Builds the block of facts every agent sees, so the debate matches the dashboard."""
from app.models import CalcResult, Company, Rule

NAMES = {
    "max_leverage": "Maximum leverage (total debt / EBITDA)",
    "max_net_leverage": "Maximum net leverage ((total debt - cash) / EBITDA)",
    "min_coverage": "Minimum interest coverage (EBITDA / interest)",
}


def money(amount: float) -> str:
    return f"${amount / 1e9:.2f}B" if abs(amount) >= 1e9 else f"${amount / 1e6:,.0f}M"


def ratio(value: float | None) -> str:
    return "not meaningful (EBITDA is zero or negative)" if value is None else f"{value:.2f}x"


def uses_net_leverage(company: Company) -> bool:
    return any(rule.type == "max_net_leverage" for rule in company.rules)


def schedule_text(rule: Rule) -> str:
    """'5.25x through 2025, 5.00x in 2026, 4.75x in 2027, 4.50x from 2028 on'"""
    steps = sorted(rule.schedule, key=lambda step: step.year)
    parts = []
    for index, step in enumerate(steps):
        when = f"through {step.year}" if index == 0 else f"from {step.year} on" if index == len(steps) - 1 else f"in {step.year}"
        parts.append(f"{step.threshold:.2f}x {when}")
    return ", ".join(parts)


def build_briefing(company: Company, calc: CalcResult, earnings_drop_pct: float, refi_rate_pct: float) -> str:
    facts = company.facts
    checks = {check.type: check for check in calc.rule_checks}
    due_by_year = {point.year: point.debt_due for point in calc.wall}

    rule_lines = []
    for rule in company.rules:
        check = checks[rule.type]
        limit = "at least" if rule.type == "min_coverage" else "at most"
        rule_lines.append(
            f"- {NAMES[rule.type]}, credit agreement §{rule.section}: must be {limit} "
            f"{rule.threshold:.2f}x. Value in this scenario: {ratio(check.value)}. "
            f"Result: {'PASS' if check.passed else 'FAIL'}.\n  Contract sentence: \"{rule.quote}\""
        )
        if len(rule.schedule) > 1:
            last = max(rule.schedule, key=lambda step: step.year)
            would_pass = check.value is not None and check.value <= last.threshold
            due = due_by_year.get(last.year, 0)
            rule_lines.append(
                f"  This limit tightens over time: {schedule_text(rule)}. "
                f"Against the {last.year} limit of {last.threshold:.2f}x, this scenario's {ratio(check.value)} "
                f"would {'PASS' if would_pass else 'FAIL'}."
                + (f" {last.year} is also the year {money(due)} of debt comes due." if due else "")
            )
    wall_lines = [
        f"- {point.label}: {money(point.debt_due)} of debt due, {money(point.cash_available)} of cash available"
        + (f" (short by {money(point.debt_due - point.cash_available)}, must be refinanced)" if point.debt_due > point.cash_available else "")
        for point in calc.wall
    ]
    sources = ["10-K income statement", "10-K cash flow statement", "10-K balance sheet", "10-K debt footnote",
               "What-if calculator", "Maturity wall"] + [f"Credit agreement §{rule.section}" for rule in company.rules]
    failed = sum(not check.passed for check in calc.rule_checks)
    if uses_net_leverage(company):
        leverage_line = f"- Net leverage (the ratio the loan rule tests): {ratio(calc.net_leverage)}"
    else:
        leverage_line = f"- Leverage: {ratio(calc.leverage)}"

    return f"""BRIEFING: {company.name} ({company.ticker}), fiscal year {company.fiscal_year}

Reported numbers (from the 10-K):
- Cash: {money(facts.cash)}
- Total debt: {money(facts.total_debt)}
- Net debt (total debt - cash): {money(facts.total_debt - facts.cash)}
- Undrawn revolver: {money(facts.revolver)}
- EBITDA: {money(facts.ebitda)}
- Interest expense: {money(facts.interest)}
- Operating cash flow: {money(facts.ocf)}, capex: {money(facts.capex)}, free cash flow: {money(facts.ocf - facts.capex)}

Scenario being judged: earnings decline of {earnings_drop_pct:g}%, debt refinanced at {refi_rate_pct:.2f}%.

Numbers in this scenario (from the what-if calculator, these are the ones to judge):
- EBITDA: {money(calc.ebitda)}
- Annual interest: {money(calc.interest)}
- Free cash flow per year: {money(calc.fcf)}
{leverage_line}
- Interest coverage: {ratio(calc.coverage)}

Loan rules (covenants): {failed} of {len(calc.rule_checks)} FAIL in this scenario.
{chr(10).join(rule_lines)}

Maturity wall (cash available = cash + cumulative free cash flow + revolver):
{chr(10).join(wall_lines)}

Allowed source labels:
{chr(10).join('- ' + label for label in sources)}"""
