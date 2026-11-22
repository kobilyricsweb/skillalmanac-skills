# Notes from the 14 Oct cache incident (raw, from the channel)

- 02:10 alert "cache hit rate < 40%" fired for the `sessions` Redis cluster
- Symptom: login p95 went from 180 ms to 2.4 s, database CPU at 90%
- Dana checked `redis-cli -h sessions-1 info stats` and saw evicted_keys climbing fast
- Cause: a deploy at 01:50 doubled session payload size; maxmemory 2 GB reached
- Fix applied 02:35: raised maxmemory to 4 GB with `redis-cli -h sessions-1 config set maxmemory 4gb`, then ran the same on sessions-2
- Hit rate back above 90% by 02:50; login p95 back to 190 ms at 03:00
- Did not roll the deploy back; unsure whether that would have been faster
- Escalation used: paged platform on-call (rota "platform-oncall" in the paging tool); Dana is not on that rota
- Open question: nobody knows how to persist the new maxmemory across restarts (config rewrite not tried)
