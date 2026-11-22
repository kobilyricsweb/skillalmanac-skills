Wrote geo-pipeline/AGENTS.md using the agent-instruction-files skill.

Based on: Makefile, .github/workflows/ci.yml (command order, generated-code check), pyproject.toml (ruff line length, pinned dev deps, Python version), docker-compose.yml (port 54329), the header of geo/generated/schema.py, the docstring in geo/loader.py (lon/lat rule), and tests/conftest.py (DB-required failure mode). README content is linked, not repeated. No existing instruction files were found; no secrets were included (the dev DB password stays in docker-compose.yml).
