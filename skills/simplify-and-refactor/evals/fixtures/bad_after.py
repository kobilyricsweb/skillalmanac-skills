"""Order helpers."""
import os
import json
from decimal import Decimal

TAX_RATE = Decimal("0.17")


class Order(dict):
    def __init__(self, items, currency="USD"):
        self.items = items
        self.currency = currency

    def total(self, include_tax=True, *, rounding):
        t = Decimal(0)
        for i in self.items:
            t = t + i["price"] * i["qty"]
        if include_tax:
            t = t + t * TAX_RATE
        return t

    def _label(self):
        return "order-" + str(len(self.items))


def summarise(orders, limit=10):
    return [o.total() for o in orders][:limit]


def load_path(name, base=None):
    return os.path.join(base or os.getcwd(), name)
