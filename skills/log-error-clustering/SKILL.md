---
name: log-error-clustering
description: Turns a large application, CI or server log into a ranked table of distinct error signatures with counts, first and last seen, rate over time, a sample line, the stack head and a triage order, using a standard-library script that masks numbers, ids, paths and secrets before grouping and can compare against a before-deploy log. Use when the user pastes or points at a huge log and asks what is failing, which errors are new, what changed after a deploy, or to group, dedupe or summarise errors. Do not use for hunting one known bug (use a debugging skill), redacting a file for sharing, writing log statements or fetching logs from a service.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only, and reads local files only. No network access is used. Without Python, use the shell fallback in the Script section.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Log error clustering

A log with 400,000 lines usually holds a handful of distinct errors. This skill finds them with a script, ranks them, and reports what is new or accelerating. Never read the raw log into the conversation: run the script and read its table.

## Workflow

```
- [ ] 1 Fix the scope: files, time window, a baseline if one exists
- [ ] 2 Run cluster_logs.py
- [ ] 3 Check warnings and stats before trusting any count
- [ ] 4 Read the top clusters in triage order
- [ ] 5 Pull context for the top few with grep on one id, not by reading the log
- [ ] 6 Report in the fixed shape
```

1. **Scope.** Get the log path(s), the window of interest (the incident hours) and, if the user mentions a deploy or "it worked yesterday", a baseline log from before. Rotated files for one service go in one run: `LOG1 LOG2`. A baseline is a separate `--baseline` file, never a rotated sibling.
2. **Run** (from the skill folder; the script writes nothing unless `--out` is given):

```bash
python scripts/cluster_logs.py app.log --since 2026-11-20T10:00:00Z --until 2026-11-20T12:00:00Z --baseline before.log --top 20
```

   With a `--since` and no `--baseline`, anything not seen earlier in the same file is marked new. Add `--min-level warning` when the user suspects warnings, `--include-unknown` for logs without level words (see step 3). The output is strict JSON; `--out report.json` saves it, and the script refuses any `--out` that is one of its input logs, even with `--force`.
3. **Check before trusting.** Read `warnings` and `stats` first:

| Signal | Meaning | Do |
|---|---|---|
| exit code 1, or `unparseable_share` above 0.5 | most lines are not log records | say counts are unreliable; try `--format plain` or `--format jsonl`; ask for the log format |
| `unparseable_share` 0.2 to 0.5 | counts are a lower bound | report it next to every count; look at `unparseable_examples` |
| `records_by_level` is all `unknown`, `in_scope` is 0 | no level words (syslog, access logs) | rerun with `--include-unknown`; clusters will mix levels, say so |
| `level_inferred` above 0 | a record without a level carried a traceback and was counted as error | mention it |
| `backward_jumps` above 0 | clock skew or merged hosts | first and last seen and rates are approximate; compare counts only |
| warning "no time zone" | naive times were read as UTC | confirm the zone before quoting hours to the user |
| `no_time_records` equals `records` | no timestamps | no rate, trend or first/last; rank by count only |
| `excluded_by_window` large | the window is narrow or the log is from another day | check the window against `window.start` and `window.end` |

4. **Read in triage order.** The script already sorts `clusters`; the rule behind `triage_rank`:

| Tier | Condition | Why first |
|---|---|---|
| 0 | `new_vs_baseline` is true | an error that did not exist before is the best lead for what changed |
| 1 | `trend` is `burst` or `rising` | still getting worse while you read |
| 2 | everything else | by `count` descending, ties by earliest `first_seen` |

   `trend` labels: `burst` = at least 10 events and at least half in one bucket; `rising` = second half of the window has at least twice the first half and at least 3 more events; `falling` the mirror; `too_few` = fewer than 6 timed events (no trend claimed); `no_time`. These are fixed thresholds, not statistics.
5. **Context.** For each of the top 3 to 5 clusters read `sample` and `stack_head`, then take one concrete id or value from the sample and `grep -n` it in the log with a few lines of context. Do not conclude from a signature alone: the placeholders hide the variable part, which is often the clue (one host, one customer).
6. **Report** in this shape and nothing longer:

```
Scope: <files, window, baseline or none>; <records> records, <in_scope> in scope
Reliability: <unparseable share, time zone assumption, skew, anything from warnings>
Triage: 1..N, one line each: <rank> <signature> | <count> | <first..last seen> | <trend> | <new or not>
Vanished since baseline: <signatures, or none>
Likely order of investigation: <2-3 sentences; hypotheses, labelled as hypotheses>
Not checked: <what the script cannot see>
```

## Reading clusters correctly

- Count is not impact. A silent 40,000-line retry loop can matter less than 3 lines of `critical` data corruption. Look at `level` before `count`; `critical` always gets mentioned.
- A cascade shows as several rising clusters. The one with the earliest `first_seen` among them is the first suspect; the rest are often consequences. This is a hypothesis for the debugging step, not a finding.
- `signature || ExceptionName` means the same message with different exception classes was kept apart on purpose.
- `merged_variants` lists signatures folded in by the similarity merge (default 0.85 on token sets, messages of at least 5 tokens). If two merged variants are really different problems, rerun with `--merge-threshold 1.0` to see them separately.
- A signature that looks too general (`Failed <STR>`) is hiding detail: widen with `grep` on the sample, or report the variants you find, not a new signature.
- To investigate the cause of one error in depth, hand the cluster to the debugging workflow. To share samples outside the team, see the Secrets paragraph.

## Secrets

Everything printed (signature, sample, stack head) passes a content-based mask: cloud access keys, API tokens, JWTs, bearer and basic credentials, `password=`/`token=`/`secret=` style values, credentials in URLs, private-key headers, emails and long opaque tokens. `stats.secrets_masked` counts what was masked by kind. The mask is pattern-based and can miss a secret in an unusual shape, so say so before the output is pasted into a ticket or sent to a third party; for a formal redaction use the redaction skill. The log file itself is never changed.

## Script

`scripts/cluster_logs.py`: run it, do not edit it to change a result. Reads only the files named; stdlib only; no network. Exit 0 = report produced, 1 = report produced but unreliable (no records or over half the lines unparseable), 2 = usage error, missing file or refused output path. Key flags: `--format auto|plain|jsonl`, `--min-level`, `--include-unknown`, `--since/--until`, `--baseline`, `--year` (syslog stamps have no year), `--bucket-seconds`, `--merge-threshold`, `--top`, `--out`. Output fields per cluster: `id, triage_rank, triage_reason, signature, level, count, first_seen, last_seen, rate_per_min, peak, histogram (24 slots), trend, new_vs_baseline, baseline_count, sample, stack_head, merged_variants`; plus `stats`, `warnings`, `window`, `vanished`.

Read [references/signature-rules.md](references/signature-rules.md) only when a format is not parsed, a level is wrong, or a signature merges or splits badly: it holds the level mapping, supported timestamp shapes, masking order and merge rules.

If Python is unavailable, approximate by hand and say it is approximate:

```bash
grep -E ' (ERROR|FATAL|CRITICAL) ' app.log | sed -E 's/[0-9]+/N/g; s#/[^ ]+#PATH#g' | cut -c1-200 | sort | uniq -c | sort -rn | head -30
```

This gives counts only, with no time, trend, baseline or secret masking.

## Limits

- English level words only (`ERROR`, `WARN`, `severe`, ...). Single-letter glog levels and access-log status codes are not read as levels.
- Lines that are neither a record start nor an indented or stack-looking continuation count as unparseable, so multi-line messages written without indentation are undercounted.
- Digits are masked everywhere, so `web1` and `web2` become one signature; use `grep` on the sample to separate hosts.
- Signatures are cut at 200 characters. Counts are log records, not users or requests.
- Naive timestamps are read as UTC. Trend and burst thresholds are fixed working values.
- About 25,000 lines per second on a laptop; very large files take minutes. Over 20,000 distinct signatures the rest are counted but not clustered.
