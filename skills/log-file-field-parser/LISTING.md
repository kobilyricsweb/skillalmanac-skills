# Log File Field Parser

## One line

Splits a text or JSON-lines log into timestamp, level and message, then reports level counts, unparsed lines, the most repeated messages and a first-occurrence timeline.

## What it does

The bundled script reads one local log file without changing it. Each non-blank line is matched against ISO 8601 and syslog timestamp patterns and against the level words DEBUG, INFO, WARNING, WARN, ERROR, ERR, CRITICAL and FATAL. JSON-lines input is read through its usual timestamp, level and message keys. Digits in each message are replaced with a hash before counting, so requests that differ only by an id collapse into one row.

The output is one JSON object: totals, counts for each of the five levels, up to 50 unparsed lines with a reason code, the top 10 repeated messages, and a timeline of the first 50 distinct messages in order of first appearance. An optional CSV holds every distinct message with its count and first and last timestamp. The CSV path must be new, and it must sit outside the input file's folder.

## When to use

Use it when a person has a log export and wants to know which levels dominate, which messages repeat, or when a failure first appeared. It suits application logs, worker logs and service logs with one event per line, up to 2 MB. The timeline answers "when did this message first show up" without scrolling the raw file.

## When not to use

Do not use it for live tailing, for logs held in a cloud service, or for files that are compressed, binary or not UTF-8. It does not group multi-line stack traces with their first line; each continuation line is counted as unparsed. It does not redact secrets, so do not treat its output as safe to share without review.

## Requirements

Python 3.9 or later, standard library only. No network access and no additional packages. The input must be a readable text file of at most 2,097,152 bytes. Writing a CSV needs an existing folder and a file name that does not yet exist.

## Example

Command, run on the 30-line sample that ships with the skill:

```
python -I "<skill-folder>/scripts/log_parse.py" "<skill-folder>/fixtures/mixed_service.txt"
```

Output (stdout, exit code 1 because the sample has six ERROR lines):

```json
{
  "input_lines": 30,
  "parsed_lines": 27,
  "unparsed_lines": 3,
  "levels": {
    "DEBUG": 5,
    "INFO": 12,
    "WARNING": 4,
    "ERROR": 6,
    "CRITICAL": 0
  },
  "unparsed": [
    {
      "line": 14,
      "reason": "NO_TIMESTAMP",
      "text": "at handler (app.js:88)"
    },
    {
      "line": 22,
      "reason": "NO_LEVEL",
      "text": "Nov 20 10:00:23 worker-1 retrying job, no level here"
    },
    {
      "line": 28,
      "reason": "NO_TIMESTAMP",
      "text": "--- end of batch 7 ---"
    }
  ],
  "distinct_messages": 15,
  "top_messages": [
    {
      "rank": 1,
      "count": 6,
      "message": "service=api request id=# completed status=#"
    },
    {
      "rank": 2,
      "count": 3,
      "message": "service=api request id=# failed status=#"
    },
    {
      "rank": 3,
      "count": 2,
      "message": "service=api Slow query took # ms"
    },
    {
      "rank": 4,
      "count": 2,
      "message": "service=api cache miss key=user:#"
    },
    {
      "rank": 5,
      "count": 2,
      "message": "service=api Retry scheduled attempt=# for id=#"
    },
    {
      "rank": 6,
      "count": 2,
      "message": "service=db connection lost after # s"
    },
    {
      "rank": 7,
      "count": 2,
      "message": "service=db reconnected after # attempts"
    },
    {
      "rank": 8,
      "count": 1,
      "message": "service=api Starting worker pool size=#"
    },
    {
      "rank": 9,
      "count": 1,
      "message": "service=api Loaded config from /etc/app/config.yaml"
    },
    {
      "rank": 10,
      "count": 1,
      "message": "service=api Listening on port #"
    }
  ],
  "timeline_total": 15,
  "timeline": [
    {
      "first_line": 1,
      "first_timestamp": "2026-11-20T10:00:01Z",
      "last_timestamp": "2026-11-20T10:00:01Z",
      "count": 1,
      "message": "service=api Starting worker pool size=#"
    },
    {
      "first_line": 2,
      "first_timestamp": "2026-11-20T10:00:02Z",
      "last_timestamp": "2026-11-20T10:00:02Z",
      "count": 1,
      "message": "service=api Loaded config from /etc/app/config.yaml"
    },
    {
      "first_line": 3,
      "first_timestamp": "2026-11-20T10:00:03Z",
      "last_timestamp": "2026-11-20T10:00:03Z",
      "count": 1,
      "message": "service=api Listening on port #"
    },
    {
      "first_line": 4,
      "first_timestamp": "2026-11-20T10:00:05Z",
      "last_timestamp": "2026-11-20T10:00:11Z",
      "count": 2,
      "message": "service=api Slow query took # ms"
    },
    {
      "first_line": 5,
      "first_timestamp": "2026-11-20T10:00:06Z",
      "last_timestamp": "2026-11-20T10:00:25Z",
      "count": 6,
      "message": "service=api request id=# completed status=#"
    },
    {
      "first_line": 6,
      "first_timestamp": "2026-11-20T10:00:07Z",
      "last_timestamp": "2026-11-20T10:00:14Z",
      "count": 3,
      "message": "service=api request id=# failed status=#"
    },
    {
      "first_line": 7,
      "first_timestamp": "2026-11-20T10:00:08Z",
      "last_timestamp": "2026-11-20T10:00:26Z",
      "count": 2,
      "message": "service=api cache miss key=user:#"
    },
    {
      "first_line": 12,
      "first_timestamp": "2026-11-20T10:00:13Z",
      "last_timestamp": "2026-11-20T10:00:13Z",
      "count": 1,
      "message": "service=api cache hit key=user:#"
    },
    {
      "first_line": 16,
      "first_timestamp": "2026-11-20T10:00:17Z",
      "last_timestamp": "2026-11-20T10:00:30Z",
      "count": 2,
      "message": "service=api Retry scheduled attempt=# for id=#"
    },
    {
      "first_line": 17,
      "first_timestamp": "2026-11-20T10:00:18Z",
      "last_timestamp": "2026-11-20T10:00:27Z",
      "count": 2,
      "message": "service=db connection lost after # s"
    },
    {
      "first_line": 18,
      "first_timestamp": "2026-11-20T10:00:19Z",
      "last_timestamp": "2026-11-20T10:00:28Z",
      "count": 2,
      "message": "service=db reconnected after # attempts"
    },
    {
      "first_line": 19,
      "first_timestamp": "Nov 20 10:00:20",
      "last_timestamp": "Nov 20 10:00:20",
      "count": 1,
      "message": "worker-# job nightly-export started"
    },
    {
      "first_line": 20,
      "first_timestamp": "Nov 20 10:00:21",
      "last_timestamp": "Nov 20 10:00:21",
      "count": 1,
      "message": "worker-# job nightly-export batch # of #"
    },
    {
      "first_line": 21,
      "first_timestamp": "Nov 20 10:00:21",
      "last_timestamp": "Nov 20 10:00:21",
      "count": 1,
      "message": "worker-# job nightly-export failed on batch #"
    },
    {
      "first_line": 30,
      "first_timestamp": "Nov 20 10:00:31",
      "last_timestamp": "Nov 20 10:00:31",
      "count": 1,
      "message": "worker-# job nightly-export finished"
    }
  ],
  "csv_path": null,
  "csv_rows": 0
}
```

## Limits

- Secrets, tokens and personal data in messages are printed as they appear. The script masks digits only.
- Multi-line entries such as stack traces are not joined; their continuation lines are listed as unparsed with reason NO_TIMESTAMP.
- Level words are recognized only in uppercase in text lines. A lowercase "error" in a text line is ignored.
- Syslog timestamps carry no year, so they cannot be sorted across years. The timeline keeps file order and shows timestamps as text.
- Timestamps are not converted to a common time zone.
- Epoch-number timestamps in JSON lines are not recognized and count as NO_TIMESTAMP.
- CSV cells are written without spreadsheet escaping, so a message that begins with an equals sign may run as a formula in a spreadsheet program.
- The script does not check that the log is complete, that the clock is correct, or that the events are true. It reports what the lines say.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
