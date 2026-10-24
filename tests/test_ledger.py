from decimal import Decimal

import pytest

from tokacct.ledger import Ledger, Prices


def test_default_prices_illustrative():
    p = Prices()
    assert p.input_per_million == Decimal("0.50") and p.output_per_million == Decimal("1.50")
    assert "illustrative" in p.as_of


@pytest.mark.parametrize(
    "tin,tout,expected",
    [(0, 0, "0"), (1_000_000, 0, "0.5"), (0, 1_000_000, "1.5"), (20, 30, "0.000055"), (8000, 1000, "0.0055")],
)
def test_cost(tin, tout, expected):
    assert Prices().cost(tin, tout) == Decimal(expected)


def test_output_three_times_input():
    p = Prices()
    assert p.cost(0, 1000) == 3 * p.cost(1000, 0)


@pytest.mark.parametrize("kw", [{"input_per_million": -0.1}, {"output_per_million": -1}, {"input_per_million": "nan"}, {"output_per_million": "inf"}])
def test_negative_or_bad_price_rejected(kw):
    with pytest.raises(ValueError):
        Prices(**kw)


def test_float_price_converted():
    assert Prices(input_per_million=0.25).input_per_million == Decimal("0.25")


@pytest.mark.parametrize("tin,tout", [(-1, 0), (0, -1), (1.5, 0), (True, 0), ("5", 0)])
def test_bad_token_counts(tin, tout):
    with pytest.raises(ValueError):
        Prices().cost(tin, tout)


def test_bad_month():
    for month in ["2026-13", "2026-1", "26-01", "", "2026-00"]:
        with pytest.raises(ValueError):
            Ledger().record("a", month, 1, 1)


def test_customer_required():
    with pytest.raises(ValueError):
        Ledger().record("", "2026-10", 1, 1)


@pytest.fixture
def led():
    lg = Ledger()
    lg.record("Copperleaf Studios", "2026-09", 1_000_000, 0)
    lg.record("Copperleaf Studios", "2026-10", 0, 1_000_000)
    lg.record("Northgate Tutors", "2026-10", 2_000_000, 2_000_000)
    return lg


def test_by_customer(led):
    assert led.by_customer() == {"Copperleaf Studios": Decimal("2.0"), "Northgate Tutors": Decimal("4.0")}


def test_by_month(led):
    assert led.by_month() == {"2026-09": Decimal("0.5"), "2026-10": Decimal("5.5")}


def test_by_customer_month(led):
    assert led.by_customer_month()[("Northgate Tutors", "2026-10")] == Decimal("4.0")


def test_total_and_split(led):
    s = led.split()
    assert led.total() == Decimal("6.0") == s["input_cost"] + s["output_cost"]


def test_empty_ledger():
    assert Ledger().total() == 0 and Ledger().by_customer() == {}


def test_decimal_no_float_drift():
    lg = Ledger()
    for _ in range(10_000):
        lg.record("a", "2026-10", 1, 1)
    assert lg.total() == Decimal("0.02")
