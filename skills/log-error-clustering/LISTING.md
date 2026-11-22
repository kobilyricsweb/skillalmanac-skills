# Listing page content: log-error-clustering

**One line:** Turns a huge log into a ranked table of distinct error signatures, with counts, timing and a triage order.

## What it does

The skill gives an agent a six-step procedure and a script that reads a log without loading it into the conversation. The script parses plain-text and JSON-lines logs, attaches stack traces to their error line, masks numbers, ids, paths, quoted strings and secrets to build a signature per error, groups identical signatures, folds near-identical long messages together, and records count, first and last seen, a 24-slot rate histogram, a sample line and the head of the stack. Given a second log (before a deploy) it marks each signature new or known and lists signatures that vanished. A decision table says what to do about unparseable lines, clock skew and missing levels, and a fixed rule orders the result: new first, then rising or bursting, then by count.

## Capabilities

- `scripts/cluster_logs.py`: strict-JSON report of clusters with `signature`, `count`, `first_seen`, `last_seen`, `rate_per_min`, `peak`, `histogram`, `trend`, `new_vs_baseline`, `baseline_count`, `sample`, `stack_head`, `merged_variants`, plus `stats`, `warnings` and `vanished`
- Time window (`--since`, `--until`), level floor, baseline comparison, syslog and epoch timestamps, UTF-16 files
- Secret masking of every printed string, with a count by kind
- A reading guide: cascades, count versus impact, when a merge or split is wrong
- A fixed report shape that includes reliability and what was not checked

## When to use

You have a long application, CI or server log and ask what is failing, which errors are new, what changed after a deploy, or want errors grouped, deduplicated or summarised.

## When not to use

- Chasing one known bug to its cause: use a debugging skill; this skill only tells you which error to start with.
- Redacting a file before sharing: the output masks secrets in what it prints, but it does not rewrite the log and is not a redaction tool.
- Writing or reviewing log statements, fetching logs from a service, alerting rules, access-log traffic analysis.

## How it differs from nearby skills

A debugging skill takes one failure and works out its cause. A redaction skill rewrites files to remove sensitive data. This skill sits before both: it reduces a large log to a short ranked list of distinct errors and shows which one is new or accelerating, masking secrets only in what it prints.

## Requirements

Python 3.9 or newer, standard library only. Local files only, no network. Without Python the agent uses a one-line shell fallback that gives counts only.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved conversation. What exists is the script on the saved fixtures.

1. `python scripts/cluster_logs.py evals/fixtures/after.log --baseline evals/fixtures/before.log` (27 error lines, 4 signatures), output condensed:

```
1 new compared with the baseline | payments Payment gateway returned <N> for order <N> | 2 | 10:10..10:24 | too_few | new
2 rate is burst                  | sched Worker heartbeat lost for node <N>           | 12 | 10:08:00..10:08:11 | burst | known (1 before)
3 rate is rising                 | inventory Timeout calling inventory service after <N> s | 9 | 10:00..10:23 | rising | known (2 before)
4 ranked by count                | cache Cache eviction failed for key <STR>           | 4 | 10:01..10:20 | too_few | known (4 before)
vanished: disk Disk almost full on volume <STR> (3 before, last 09:22)
```

2. `python scripts/cluster_logs.py evals/fixtures/app.log` (24 lines, 11 records, 12 stack lines attached, 1 unparseable): five clusters in order, led by `app.db Connection refused to <IP> after <N> retries` (4); two `Unhandled exception` messages with identical text stay apart because their exception classes are `KeyError` and `ValueError`; the login failure line prints as `... for <EMAIL> password=<SECRET> token=<SECRET>`.

## Limits

- English level words only; glog single-letter levels and access-log status codes are not read as levels.
- Non-indented multi-line messages count as unparseable lines.
- Digits are masked everywhere, so `web1` and `web2` share a signature.
- Naive timestamps are read as UTC; trend and burst thresholds are fixed working values.
- Secret masking is pattern based and can miss unusual shapes.
- About 25,000 lines per second; very large files take minutes.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and 22 script fixture cases pass with expected values worked out by hand. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, real-world log corpora, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. A user drops `after.log` and `before.log` and asks what changed after the deploy.
2. The agent runs the script; the warnings and stats are checked first.
3. The table appears: the payment gateway error is new, the heartbeat error is a 12-event burst in one minute, the inventory timeout is rising, one disk error vanished.
4. The agent greps one order id for context and reports in the fixed shape, with hypotheses labelled as hypotheses and a "not checked" line.

## FAQ seeds

- Does it need network access? No. It reads only the files you name.
- Does it change my log file? No. It refuses to write a report over any input file, even with `--force`.
- Are secrets removed from the output? Values matching known secret shapes are masked in everything printed; the mask is pattern based, so check before sharing outside the team.
- How is it different from a debugging skill? It ranks which errors exist and which are new; the debugging skill explains why one of them happens.
- Will it work on my format? Plain text with ISO, common-log, syslog or epoch times and JSON lines are supported; others are reported as unparseable lines with the share shown.
- How big a log can it take? About 25,000 lines per second; it streams, so memory stays bounded by the number of distinct signatures.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
