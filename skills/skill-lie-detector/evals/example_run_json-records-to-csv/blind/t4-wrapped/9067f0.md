```csv
city,temp_c,wind_kmh,wind_dir
Tel Aviv,24,12,W
Haifa,21,30,NW
```

- The source has no per-city timestamp, so the top-level `generated` date (2026-11-25) is left out of the CSV.
- Nested `wind` fields are flattened to `wind_kmh` and `wind_dir`.
- Values are copied as-is, with no unit conversion.
