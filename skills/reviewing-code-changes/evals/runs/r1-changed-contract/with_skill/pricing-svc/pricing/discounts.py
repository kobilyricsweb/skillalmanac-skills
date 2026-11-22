"""Discount rules."""

RATES = {"gold": 0.15, "silver": 0.10}


def calculate_discount(order_total_cents: int, tier: str) -> float:
    """Return the discount for a tier as a fraction between 0 and 1."""
    return RATES.get(tier, 0.0)
