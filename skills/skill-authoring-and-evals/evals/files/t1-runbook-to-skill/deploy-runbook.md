# Deploy runbook: orders-api

1. Run `make test`. Stop if anything fails.
2. Tag the commit `vYYYY.MM.DD-N` where N counts deploys that day.
3. Run `make release TAG=<tag>`; it builds the image and pushes it to the registry.
4. Apply the migration job first: `kubectl apply -f deploy/migrate.yaml`, wait until it completes, never deploy the app before it.
5. Roll out: `kubectl rollout restart deploy/orders-api`, then watch `kubectl rollout status` for 5 minutes.
6. If error rate on the dashboard exceeds 2% in that window, run `kubectl rollout undo deploy/orders-api` and open an incident note.
7. Post the tag and the result in the releases channel.
