import re

_WS = re.compile(r"\s+")


def parse_ids(text, separator=","):
    return [int(p.strip()) for p in text.split(separator) if p.strip()]


def clean_name(name, lower=False):
    cleaned = _WS.sub(" ", name).strip()
    return cleaned.lower() if lower else cleaned


class Registry:
    def __init__(self):
        self.items = {}

    def add(self, key, value):
        self.items[key] = value

    def get(self, key):
        return self.items[key]
