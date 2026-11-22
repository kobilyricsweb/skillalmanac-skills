# Deploy guide

Intro paragraph about deployments. We ship from the main branch every weekday, and each release is tagged with the date.

## Rollback

To roll back a release, run the rollback command and wait for the health check to pass. The previous build is kept for fourteen days so the rollback is always available to the on-call engineer.

```bash
deploy rollback --service api --to previous
deploy status --service api
deploy logs --service api --since 10m
```

## Limits

| Plan | Deploys per day |
|------|-----------------|
| Free | 5 |
| Team | 50 |
| Scale | 500 |

Deploys above the limit are queued until midnight UTC.
