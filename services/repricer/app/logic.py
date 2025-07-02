from decimal import Decimal

MIN_MARGIN = Decimal("0.15")  # 15 % ROI


def compute_price(asin: str, cost: Decimal, fees: Decimal) -> Decimal:
    """Toy algorithm: ensure 15 % ROI and round to cents.
    Replace with real competitive logic later.
    """
    raw = (cost + fees) / (1 - MIN_MARGIN)
    return raw.quantize(Decimal("0.01"))
