#!/usr/bin/env python3
"""Fetch the current temperature for a coordinate pair and cache it next to this script."""
import json
import os
import sys
from urllib.request import urlopen

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache.json")
UNITS = os.environ.get("WEATHER_UNITS", "celsius")


def main(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&current_weather=true" % (lat, lon)
    with urlopen(url, timeout=10) as response:
        data = json.load(response)
    with open(CACHE, "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    print(json.dumps({"units": UNITS, "temperature": data["current_weather"]["temperature"]}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
