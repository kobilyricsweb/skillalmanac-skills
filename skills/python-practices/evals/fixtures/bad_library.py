"""Fixture: a library module with one of each anti-pattern."""
import os
import sys
import json
from os.path import join
from typing import Optional


def load(path, seen=[]):
    full = os.path.join("data", path)
    print("loading", full)
    try:
        with open(full) as fh:
            seen.append(path)
            return json.load(fh)
    except:
        return None


def tags(extra={}, *, names=set()):
    return extra, names


def describe(value: "Optional[int]"):
    return str(value)


def main():
    print(load("a.json"))
