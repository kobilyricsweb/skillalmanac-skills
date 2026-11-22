---
trigger: model_decision
description: Use when a DAG run has failed in production and needs triage
---

# DAG failure triage

1. Find the failed task and read its log before anything else.
2. Check whether the upstream dataset landed (`platform/freshness.py --dataset <name>`).
3. If the failure is a schema change upstream, do not rerun: open a ticket for the owning team.
4. Rerun only the failed task with `airflow tasks clear`, never the whole DAG.
5. Record the incident in `docs/incidents/`.
