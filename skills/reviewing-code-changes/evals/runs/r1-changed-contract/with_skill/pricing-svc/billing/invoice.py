from pricing.discounts import calculate_discount


def invoice_total(subtotal_cents, tier):
    """Total printed on the monthly invoice."""
    pct = calculate_discount(subtotal_cents, tier)
    return subtotal_cents - subtotal_cents * pct // 100
