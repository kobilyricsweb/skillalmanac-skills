"""Smoke-test fixture A: one unused import and one duplicate import."""
import os
import json
import re
from collections import OrderedDict
from pathlib import Path
import json


def load(path):
    text = Path(path).read_text()
    return json.loads(text)


def main():
    print(os.getcwd())
    return OrderedDict()
