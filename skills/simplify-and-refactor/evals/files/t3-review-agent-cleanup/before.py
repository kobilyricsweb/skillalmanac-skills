import re
import logging

log = logging.getLogger(__name__)


def parse_ids(text, sep=","):
    out = []
    for part in text.split(sep):
        part = part.strip()
        if part:
            out.append(int(part))
    return out


def clean_name(name, lower=False):
    name = re.sub(r"\s+", " ", name).strip()
    return name.lower() if lower else name


class Registry:
    def __init__(self):
        self.items = {}

    def add(self, key, value):
        self.items[key] = value
        log.info("added %s", key)

    def get(self, key, default=None):
        return self.items.get(key, default)


def count_items(registry):
    return len(registry.items)
