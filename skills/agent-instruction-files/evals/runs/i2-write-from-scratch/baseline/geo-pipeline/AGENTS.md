# AGENTS.md

Python 3.11+ pipeline: load municipal boundary files (`geo/loader.py`), normalise (`geo/normalise.py`), publish tiles (`geo/publish.py`). Runs nightly. See README.md for background.

## Commands

- `make install` - install the package with dev extras (pytest 8.3.3, ruff 0.7.4).
- `make dev-db` - start the PostGIS container (docker compose, host port 54329). Run this before tests.
- `make test` - `pytest -q`.
- `make lint` - `ruff check geo tests`. `make fmt` - `ruff format geo tests`. Line length is 100.
- `make gen` - regenerate `geo/generated/schema.py` from `schema/geo.yaml`.

CI (pull requests) runs: install, lint, dev-db, test, then `make gen && git diff --exit-code geo/generated`. Run the same sequence locally before finishing.

## Rules

- Coordinate order is (lon, lat) everywhere, as in GeoJSON. Two production incidents came from assuming (lat, lon). Never swap it.
- Do not edit anything in `geo/generated/` by hand. To change the schema, edit `schema/geo.yaml`, run `make gen`, and commit both files. CI fails if the generated file differs from generator output.
- If every test fails with `ConnectionRefusedError`, the database is not running. Run `make dev-db`; it is not a code bug.

## Layout

- `geo/` - pipeline code; `geo/generated/` - generated, do not edit.
- `schema/geo.yaml` - schema source of truth.
- `tools/gen_schema.py` - the generator behind `make gen`.
- `tests/` - pytest suite; needs the dev database.
