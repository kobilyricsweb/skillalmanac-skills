---
name: orders-deploy
description: Deploys orders-api to the cluster with tagging, migration first, rollout watch and rollback. Use when the user asks to deploy, release or roll back orders-api. Do not use for other services.
license: Apache-2.0
---

# Orders deploy

1. Run `make test`; stop on failure.
2. Tag, release, apply the migration job and wait for it.
3. Restart the rollout and watch 5 minutes; undo above 2% errors.
