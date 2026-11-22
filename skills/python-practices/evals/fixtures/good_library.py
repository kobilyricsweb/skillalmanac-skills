"""Fixture: the same job written the way the skill asks."""
import json
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


def load(path: str, seen: Optional[list] = None) -> Optional[dict]:
    seen = [] if seen is None else seen
    full = Path("data") / path
    log.info("loading %s", full)
    try:
        seen.append(path)
        return json.loads(full.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        log.exception("could not load %s", full)
        return None
