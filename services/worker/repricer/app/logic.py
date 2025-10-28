from __future__ import annotations

from decimal import Decimal
from typing import Any

DEFAULT_MIN_ROI = Decimal("0.15")  # 15 % ROI
DEFAULT_UNDERCUT = Decimal("0.02")  # 2 % buybox gap
DEFAULT_QUANT = Decimal("0.01")  # round to cents

MIN_MARGIN = DEFAULT_MIN_ROI  # Backwards compatibility for compute_price()


def _normalize_quant(quant: Decimal) -> Decimal:
    if quant <= 0:
        return DEFAULT_QUANT
    return quant


def _strategy_order(key: str) -> int:
    order = {"min_roi": 0, "buybox_gap": 1, "map": 2}
    return order.get(key, 99)


def _applied_strategies(
    candidates: dict[str, Decimal], chosen_value: Decimal
) -> list[str]:
    applied: list[str] = []
    if "min_roi" in candidates:
        applied.append("min_roi")
    for name, value in candidates.items():
        if name == "min_roi":
            continue
        if value == chosen_value:
            applied.append(name)
    applied.sort(key=_strategy_order)
    return applied


def _serialize_candidates(
    candidates: dict[str, Decimal], quant: Decimal
) -> dict[str, Decimal]:
    quant = _normalize_quant(quant)
    return {key: value.quantize(quant) for key, value in candidates.items()}


def decide_price(
    asin: str,
    cost: Decimal,
    fees: Decimal,
    *,
    buybox: Decimal | None,
    map_price: Decimal | None,
    min_roi: Decimal,
    undercut: Decimal,
    quant: Decimal,
) -> tuple[Decimal, dict[str, Any]]:
    """
    Decide on a repricing outcome with explainability metadata.
    """
    if min_roi >= Decimal("1"):
        raise ValueError(f"min_roi must be < 1 for {asin}")

    quant = _normalize_quant(quant)

    candidates: dict[str, Decimal] = {}
    min_roi_price = (cost + fees) / (Decimal("1") - min_roi)
    candidates["min_roi"] = min_roi_price

    if buybox is not None:
        candidates["buybox_gap"] = buybox * (Decimal("1") - undercut)

    if map_price is not None:
        candidates["map"] = map_price

    chosen_value = max(candidates.values())
    final_price = chosen_value.quantize(quant)

    explain = {
        "candidates": _serialize_candidates(candidates, quant),
        "applied": _applied_strategies(candidates, chosen_value),
        "config": {
            "min_roi": min_roi,
            "undercut": undercut,
            "quant": quant,
        },
    }

    return final_price, explain


def compute_price(asin: str, cost: Decimal, fees: Decimal) -> Decimal:
    """Toy algorithm: ensure 15 % ROI and round to cents.
    Replace with real competitive logic later.
    """
    price, _ = decide_price(
        asin,
        cost,
        fees,
        buybox=None,
        map_price=None,
        min_roi=MIN_MARGIN,
        undercut=Decimal("0"),
        quant=DEFAULT_QUANT,
    )
    return price
