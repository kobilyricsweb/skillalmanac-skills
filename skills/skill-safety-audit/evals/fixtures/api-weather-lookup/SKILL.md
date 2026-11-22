---
name: api-weather-lookup
description: Looks up the current temperature for a city through a public weather API and caches the answer. Use when the user asks for the weather in a named city. Do not use for forecasts older than today.
license: Apache-2.0
metadata:
  author: Example Author
  version: "1.0.0"
  network: api.open-meteo.com
---

# API weather lookup

1. Install the one dependency: pip install tabulate
2. Run `python scripts/lookup.py <latitude> <longitude>`.
3. Read the printed JSON back to the user.

The script contacts api.open-meteo.com only and keeps one cache file inside this folder.
