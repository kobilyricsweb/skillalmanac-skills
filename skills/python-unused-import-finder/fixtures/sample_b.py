"""Smoke-test fixture B: a star import, two unused imports and one noqa-suppressed import."""
from os.path import *
import sys
import typing as t  # noqa: F401
import logging
from datetime import datetime


def stamp():
    return datetime.now()
