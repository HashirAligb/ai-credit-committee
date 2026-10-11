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
