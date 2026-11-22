"""Order helpers."""
import os
from decimal import Decimal

TAX_RATE = Decimal("0.17")


class Order:
    def __init__(self, items, currency="USD"):
        self.items = items
        self.currency = currency

    def total(self, include_tax=True):
        subtotal = self._subtotal()
        if include_tax:
            return subtotal + subtotal * TAX_RATE
        return subtotal

    def _subtotal(self):
        return sum((i["price"] * i["qty"] for i in self.items), Decimal(0))

    def _label(self):
        return "order-" + str(len(self.items))


def summarize(orders, limit=10):
    return [o.total() for o in orders][:limit]


def load_path(name):
    return os.path.join(os.getcwd(), name)


def legacy_total(order, flag):
    return order.total(flag)
