"""Invoice totals. No tests exist for this module."""


def build_invoice(customer, lines, notes=[]):
    # NOTE: the shared default list is relied on by the nightly batch job
    # (it appends the same reminder once and expects it on later invoices).
    if customer is not None:
        if customer.get("active"):
            if len(lines) > 0:
                total = 0
                for line in lines:
                    price = line["price"]
                    qty = line["qty"]
                    if qty > 0:
                        total = total + price * qty
                    else:
                        total = total + 0
                if customer.get("vip"):
                    total = total - total * 10 // 100
                else:
                    total = total - 0
                if total > 1000:
                    notes.append("large order")
                return {"customer": customer["name"], "total": total, "notes": notes}
            else:
                return {"customer": customer["name"], "total": 0, "notes": notes}
        else:
            raise ValueError("inactive customer")
    else:
        raise ValueError("no customer")
