## Contents

1. Record starts and continuations
2. Level mapping
3. Timestamp shapes
4. Masking order and placeholders
5. Near-signature merge
6. Fixing a bad split or merge

## 1. Record starts and continuations

A new record starts at a line that has a timestamp within its first 40 characters, or a level word near the start of the line. JSON object lines (when `--format` is `auto` or `jsonl`) are one record each. A line is a continuation of the previous record when it is indented, or starts with `Traceback`, `Caused by:`, `Exception in thread`, `panic:`, `goroutine N`, `... N more`, or a word ending in `Error`, `Exception`, `Exit` or `Panic`. A continuation is attached to the previous record and never counted as a line of its own. Anything else counts as unparseable.

The exception class is taken from the last continuation line that names one (Python prints the real exception last; Java prints the root cause last in `Caused by:`). It is appended to the signature after `||`.

JSON records read the message from `msg`, `message`, `event`, `log` or `text`; the level from `level`, `severity`, `lvl`, `levelname`, `severity_text`; the time from `timestamp`, `@timestamp`, `time`, `ts`, `asctime`, `datetime`; a stack from `stack`, `stack_trace`, `stacktrace`, `traceback`, `exception`.

## 2. Level mapping

| Words in the log | Class used here | Rank |
|---|---|---|
| TRACE | trace | 0 |
| DEBUG | debug | 1 |
| INFO, NOTICE | info | 2 |
| WARN, WARNING | warning | 3 |
| ERR, ERROR, SEVERE | error | 4 |
| CRIT, CRITICAL, FATAL, EMERG, EMERGENCY, ALERT, PANIC | critical | 5 |

Numeric JSON levels follow the pino and bunyan scale: 10 trace, 20 debug, 30 info, 40 warning, 50 error, 60 critical. A record with no level is `unknown` (rank below trace) and is dropped unless `--include-unknown` is given, except that an `unknown` record carrying a traceback or an exception line is promoted to `error` and counted in `level_inferred`.

A level word is recognised in brackets (`[error]`), after `level=` / `lvl=` / `severity=`, as a bare upper-case word in the first 100 characters, or at the very start of the line followed by `:` or `|`.

## 3. Timestamp shapes

| Shape | Example | Zone |
|---|---|---|
| ISO 8601, `T` or space, `-` or `/`, optional fraction (`.` or `,`) | `2026-11-20T10:00:05.123Z`, `2026-11-20 10:00:05,123` | `Z` or offset if present, else naive (read as UTC) |
| Common log format | `20/Nov/2026:10:00:05 +0000` | offset if present |
| Syslog | `Nov 20 10:15:30` | no year: `--year` is used; naive |
| Epoch seconds or milliseconds at line start | `1795168805`, `1795168805000` | UTC |
| JSON number | seconds, milliseconds, microseconds or nanoseconds, told apart by size | UTC |

A timestamp more than 60 seconds behind the largest one seen so far in the same file counts as a backward jump.

## 4. Masking order and placeholders

Secrets are masked first (see SKILL.md), then the message is normalised in this order. Order matters: URLs and paths go before bare numbers so ports and path segments leave no stray digits.

| Order | Pattern | Placeholder | Example |
|---|---|---|---|
| 1 | UUID | `<UUID>` | `3f2a9c1e-4b7d-4e2a-9a11-0c5d8e7f6a21` |
| 2 | `http(s)://host` plus port, path and query | `https://host<PATH>` (host kept) | `https://api.example.com:8443/v2/items?id=5` |
| 3 | IPv4 with optional port, full IPv6 | `<IP>` | `10.0.0.5:5432` |
| 4 | Windows path | `<PATH>` | `C:\Data\app\7.bin` |
| 5 | Unix path | `<PATH>` | `/var/lib/app/shard-12.db` |
| 6 | `0x` hex, and 8 or more hex characters containing a digit and a letter | `<HEX>` | `0x7ffd1234abcd`, `9f3a2b7c1d` |
| 7 | double-quoted string; single-quoted string not touching a word character | `<STR>` | `"user:42"`, `'abc'` (not the apostrophe in `can't`) |
| 8 | any remaining number | `<N>` | `1532`, `3.11` |

Then whitespace is collapsed and the result cut at 200 characters. An empty message becomes `<empty>`.

## 5. Near-signature merge

After exact grouping, clusters are visited from largest to smallest. A cluster merges into an earlier, larger one when all of these hold: same level class (error, critical, warning or other), same exception class, both messages have at least 5 tokens, the token counts differ by at most a factor of 1.5, and the Jaccard similarity of the two token sets is at least the threshold (default 0.85). A one-word difference therefore merges only messages of about 13 tokens or more at 0.85; at 0.7 it merges messages of about 6 tokens. The merge is skipped (with a warning) above 2,000 distinct signatures.

## 6. Fixing a bad split or merge

| Symptom | Cause | Action |
|---|---|---|
| The same error appears as several clusters differing in one word | an unmasked variable word (hostname, tenant) | lower `--merge-threshold` to 0.7, or report them as one and name the variable |
| Two different problems share a cluster | merge too eager | `--merge-threshold 1.0` |
| A cluster named `Failed <STR>` | message is a template with the detail in quotes | grep the sample for the detail |
| Many clusters that differ only by a stack-trace line | the exception class is the last line, the message is generic | use the exception class and the `stack_head` to group by hand |
| Everything is `unknown` | no level words | `--include-unknown` |
