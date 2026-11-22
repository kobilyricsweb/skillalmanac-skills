"""Small stats helpers used by report scripts."""


def avg(values):
    if not values:
        return 0
    return sum(values) / len(values)


def pct(part, whole):
    return int(part / whole * 100)
