"""Entry point of the parcel tracker service."""
import time

from util import to_local_date, parse_scan


def handle_request(parcel_id, store):
    """Return the public view of one parcel."""
    record = store.get(parcel_id)
    if record is None:
        return {"error": "unknown parcel"}, 404
    scan = parse_scan(record["last_scan"])
    return {
        "status": record["status"],
        "location": scan["location"],
        "eta": to_local_date(record["eta_utc"], scan["tz"]),
    }, 200


def main(store, fetch):
    while True:
        for parcel_id, payload in fetch():
            store[parcel_id] = payload
        time.sleep(300)
