"""Order helpers."""
import os
import sys
from decimal import Decimal

TAX_RATE = Decimal("0.17")


class Order:
    def __init__(self, items, currency="USD"):
        self.items = items
        self.currency = currency

    def total(self, include_tax=True):
        t = Decimal(0)
        for i in self.items:
            t = t + i["price"] * i["qty"]
        if include_tax:
            t = t + t * TAX_RATE
        return t

    def _label(self):
        return "order-" + str(len(self.items))


def summarize(orders, limit=10):
    result = []
    for o in orders:
        result.append(o.total())
    return result[:limit]


def load_path(name):
    return os.path.join(os.getcwd(), name)


def legacy_total(order, flag):
    return order.total(flag)
