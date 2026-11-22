# geo-pipeline

Python 3.11+ pipeline: load boundary files, normalise, publish tiles (see README.md for the overview).

## Commands

- `make install` installs with dev extras (pytest, ruff pinned in pyproject.toml).
- `make dev-db` starts the PostGIS container. Run it before `make test`: tests connect to port 54329, and without the container every test fails with ConnectionRefusedError, which is not a code bug.
- `make test` runs `pytest -q`.
- `make lint` runs `ruff check geo tests`; `make fmt` formats (line length 100, set in pyproject.toml).
- CI runs install, lint, dev-db, test, then the generated-code check, in that order. Run the same before opening a PR.

## Never edit generated code

`geo/generated/schema.py` is generated from `schema/geo.yaml`. Edit the YAML, then run `make gen`. CI fails if the committed file differs from generator output (`make gen && git diff --exit-code geo/generated`).

## Coordinates

Order is (lon, lat) everywhere, as in GeoJSON. Two production incidents came from assuming (lat, lon). Do not swap, including in tests and new function signatures.
