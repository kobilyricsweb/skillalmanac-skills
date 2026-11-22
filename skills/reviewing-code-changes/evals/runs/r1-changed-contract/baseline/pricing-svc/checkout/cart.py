from pricing.discounts import calculate_discount


def cart_total(items: list[dict], user: dict) -> int:
    subtotal = sum(item["price_cents"] * item["qty"] for item in items)
    discount = calculate_discount(subtotal, user["tier"])
    return round(subtotal * (1 - discount))
