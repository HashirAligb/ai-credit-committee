import json
from pathlib import Path

from app.models import Company
from app.numbers.calculator import calculate


COMPANY = Company.model_validate(json.loads(
    (Path(__file__).parents[2] / "data/companies/PZCO.json").read_text()
))


def test_pizza_baseline():
    result = calculate(COMPANY, 0, 5)
    assert result.leverage == 4
    assert result.coverage == 5
    assert all(check.passed for check in result.rule_checks)


def test_pizza_stress():
    result = calculate(COMPANY, 30, 10)
    assert result.leverage == 400 / 70
    assert result.coverage == 1.75
    assert not any(check.passed for check in result.rule_checks)


def test_wall_covers_every_year():
    wall = calculate(COMPANY, 0, 5).wall
    assert [point.year for point in wall] == [2025, 2026, 2027, 2028]
    assert [point.debt_due for point in wall] == [0, 0, 0, 400e6]
    # cash 100M + 50M of FCF per year, no revolver
    assert [point.cash_available for point in wall] == [150e6, 200e6, 250e6, 300e6]


def test_wall_under_stress():
    wall = calculate(COMPANY, 30, 10).wall
    # stressed FCF = 50M - 30M - 20M = 0, so cash never builds
    assert [point.cash_available for point in wall] == [100e6] * 4
