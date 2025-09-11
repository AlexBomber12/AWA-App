from decimal import Decimal

from services.worker.repricer.app.logic import compute_price


def test_compute_price_float():
    price = compute_price("B0", Decimal("10"), Decimal("2"))
    assert isinstance(float(price), float)
    assert price >= Decimal("12")
