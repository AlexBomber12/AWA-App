from decimal import Decimal

from services.worker.repricer.app.logic import (
    DEFAULT_MIN_ROI,
    DEFAULT_QUANT,
    DEFAULT_UNDERCUT,
    decide_price,
)


def _decide(
    *,
    cost: Decimal,
    fees: Decimal,
    buybox: Decimal | None = None,
    map_price: Decimal | None = None,
) -> tuple[Decimal, dict]:
    return decide_price(
        "ASIN1234567",
        cost,
        fees,
        buybox=buybox,
        map_price=map_price,
        min_roi=DEFAULT_MIN_ROI,
        undercut=DEFAULT_UNDERCUT,
        quant=DEFAULT_QUANT,
    )


def test_decide_price_returns_min_roi_when_no_buybox():
    price, explain = _decide(cost=Decimal("10"), fees=Decimal("2"))
    assert price == Decimal("14.12")
    assert explain["applied"] == ["min_roi"]


def test_decide_price_uses_buybox_when_it_beats_min_roi():
    price, explain = _decide(
        cost=Decimal("10"), fees=Decimal("2"), buybox=Decimal("16")
    )
    assert price == Decimal("15.68")
    assert explain["applied"] == ["min_roi", "buybox_gap"]


def test_decide_price_respects_map_floor():
    price, explain = _decide(
        cost=Decimal("10"),
        fees=Decimal("2"),
        buybox=Decimal("15"),
        map_price=Decimal("20"),
    )
    assert price == Decimal("20.00")
    assert explain["applied"] == ["min_roi", "map"]


def test_decide_price_rounds_to_cents():
    price, _ = _decide(cost=Decimal("10.01"), fees=Decimal("1.03"))
    assert price.quantize(Decimal("0.01")) == price


def test_decide_price_explain_contains_candidates():
    price, explain = _decide(
        cost=Decimal("10"), fees=Decimal("2"), buybox=Decimal("16")
    )
    assert price == explain["candidates"]["buybox_gap"]
    assert "min_roi" in explain["candidates"]
    assert explain["config"]["min_roi"] == DEFAULT_MIN_ROI
