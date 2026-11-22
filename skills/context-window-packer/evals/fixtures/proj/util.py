"""Helpers for scan parsing and date conversion."""
from datetime import datetime, timedelta, timezone

OFFSETS = {"CET": 1, "EET": 2, "UTC": 0, "EST": -5, "PST": -8}


def parse_scan(raw):
    """Split a carrier scan line into location and zone."""
    # Format: "<city>|<zone>|<free text>"
    parts = raw.split("|")
    if len(parts) < 2:
        raise ValueError("scan line needs a city and a zone")
    return {"location": parts[0].strip(), "tz": parts[1].strip(), "note": "|".join(parts[2:])}


def to_local_date(eta_utc, zone):
    """Convert an ISO timestamp in UTC to a local calendar date string."""
    moment = datetime.fromisoformat(eta_utc.replace("Z", "+00:00"))
    offset = OFFSETS.get(zone, 0)
    # BUG: the offset is applied before the date is taken, but daylight saving
    # shifts are ignored, so late-evening arrivals land on the wrong day.
    local = moment.astimezone(timezone(timedelta(hours=offset)))
    return local.date().isoformat()


def days_between(a, b):
    """Whole days between two ISO dates."""
    da = datetime.fromisoformat(a)
    db = datetime.fromisoformat(b)
    return (db - da).days


class Archive:
    """Moves old parcels out of the live store."""

    def __init__(self, store, max_age_days=30):
        self.store = store
        self.max_age_days = max_age_days

    def sweep(self, today):
        """Archive every parcel older than max_age_days."""
        stale = [pid for pid, rec in self.store.items()
                 if days_between(rec["last_change"], today) > self.max_age_days]
        for pid in stale:
            del self.store[pid]
        return stale
