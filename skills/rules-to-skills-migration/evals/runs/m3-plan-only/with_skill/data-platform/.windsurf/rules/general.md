---
trigger: always_on
---

- Python 3.12, managed with uv. Run things with `uv run`.
- The docs site in `docs-site/` uses pnpm.
- Airflow DAG files live in `dags/` and must not import from `notebooks/`.
- Secrets come from the vault client in `platform/secrets.py`; never read env vars for credentials.
