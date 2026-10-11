import pytest

from app.numbers.calculator import calculate
from app.numbers.routes import load_company

COMPANY = load_company("PZCO")
SILGAN = load_company("SLGN")
SILGAN_RATE = SILGAN.facts.interest / SILGAN.facts.total_debt * 100  # about 4.34%


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


def checks_by_type(result):
    return {check.type: check for check in result.rule_checks}


def test_silgan_baseline_uses_net_leverage():
    result = calculate(SILGAN, 0, SILGAN_RATE)
    checks = checks_by_type(result)
    assert SILGAN_RATE == pytest.approx(4.34, abs=0.005)
    # (4,364.7M debt - 1,080.7M cash) / 915.4M EBITDA
    assert checks["max_net_leverage"].value == pytest.approx(3.59, abs=0.005)
    assert checks["min_coverage"].value == pytest.approx(4.83, abs=0.005)
    assert all(check.passed for check in result.rule_checks)
    assert result.leverage == pytest.approx(4.77, abs=0.005)  # gross is still reported


def test_silgan_stress_fails_both_rules():
    checks = checks_by_type(calculate(SILGAN, 30, 10))
    assert checks["max_net_leverage"].value == pytest.approx(5.12, abs=0.005)
    assert checks["max_net_leverage"].threshold == 5.0
    assert not checks["max_net_leverage"].passed
    assert checks["min_coverage"].value == pytest.approx(1.47, abs=0.005)
    assert checks["min_coverage"].threshold == 3.0
    assert not checks["min_coverage"].passed


def test_silgan_wall_puts_undated_debt_in_a_final_bucket():
    wall = calculate(SILGAN, 0, SILGAN_RATE).wall
    assert [point.label for point in wall] == ["2026", "2027", "2028", "2029", "2030", "2031+"]
    assert wall[2].debt_due == 1_379_544_000
    assert wall[-1].debt_due == 709_821_000  # the year=null entry in the config
