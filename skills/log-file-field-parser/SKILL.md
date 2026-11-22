---
name: log-file-field-parser
description: Parses a text or JSON-lines log file into timestamp, level and message fields, then reports counts per level, unparsed lines, the top 10 repeating messages and a first-occurrence timeline, with an optional CSV of distinct messages. Use when a user asks to analyze log files, scan an application log for errors, count log levels, or turn raw log lines into a table. Do not use for live log tailing, remote or cloud log retrieval, redacting secrets, files over 2 MB, or compressed or binary logs.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Log File Field Parser

Use this skill to turn a raw log file into fields and counts. The script
`scripts/log_parse.py` does all parsing. Your job is to run it on the user's
file, check the exit code, and report the result in the contract below.

## Workflow

1. Confirm the input. It must be one text or JSON-lines file, UTF-8, at most
   2,097,152 bytes. Output: the input path and its size in bytes.
2. Decide on the CSV. It is optional. If the user wants one, pick a new file
   name in a folder other than the input file's folder. Output: the CSV path, or
   "none".
3. Run the script (command below). Output: the JSON report on stdout, or a
   one-line JSON error on stderr, plus the exit code.
4. Apply the decision table. Output: the status and any stop message.
5. Check the unparsed share: unparsed_lines divided by input_lines. Output: the
   percentage, rounded to one decimal.
6. Write the report in the output contract. Copy numbers from the JSON only;
   never estimate a count.

## Command

```
python -I "<skill-folder>/scripts/log_parse.py" "<input-file>" --csv "<output-csv>"
```

Omit `--csv "<output-csv>"` when no CSV is wanted. The script reads the input
only. It never overwrites a file and never writes into the input file's folder.

## Decision table

| Condition | Action |
|---|---|
| Exit 0 | Status `complete`. Report all sections. |
| Exit 1 | Status `complete`. ERROR or CRITICAL lines exist; state the ERROR and CRITICAL counts from `levels`. The top-message table has no level column, so do not attribute a level to any message. |
| Exit 2 | Status `failed`. Report the error code and stop. Do not guess a result. |
| Unparsed share above 10 percent (working value) | Add "Parse rules may not fit this format" and show the first 5 unparsed rows. |
| Unparsed share at or below 10 percent (working value) | Show the unparsed table as-is. |
| More than 10 distinct messages | Show only the top 10 table; the CSV holds the rest. |
| More than 50 distinct messages | Show the first 50 timeline rows and state the total from timeline_total. |

## Recognized fields

- Timestamps: ISO 8601 such as `2026-11-20T10:00:01Z` or `2026-11-20 10:00:01.250+01:00`,
  and syslog such as `Nov 20 10:00:21` (no year). The first match on the line is used.
- Levels: DEBUG, INFO, WARNING, WARN, ERROR, ERR, CRITICAL, FATAL, uppercase only
  in text lines. WARN maps to WARNING, ERR to ERROR, FATAL to CRITICAL.
- JSON lines: timestamp from keys timestamp, @timestamp, time, ts or date; level
  from level, severity or lvl (any case); message from message or msg.
- Masking: every run of digits in a message becomes `#` before counting, so
  `request id=1002` and `request id=1004` count as one message.

## Output contract

The script prints one JSON object. Report it as these sections, in this order:

1. **Summary**: keys `input_lines`, `parsed_lines`, `unparsed_lines`, `distinct_messages`. Add a `Status` line derived from the exit code: `complete` for exit 0 or 1, `failed` for exit 2. The JSON has no status key.
2. **Levels**: keys DEBUG, INFO, WARNING, ERROR, CRITICAL from `levels`; all five rows always appear, even at 0.
3. **Unparsed lines**: columns `line`, `reason`, `text` from `unparsed`. The `unparsed` list holds at most 50 rows; `unparsed_lines` gives the full count.
4. **Top messages**: columns `rank`, `count`, `message` from `top_messages`.
5. **Timeline**: columns `first_line`, `first_timestamp`, `last_timestamp`, `count`, `message` from `timeline`; state `timeline_total`.
6. **CSV**: `csv_path` and `csv_rows`, or "none".
7. **Open questions**: missing facts or refused items, or "none".

Timestamps in the timeline are text as found in the file; syslog values have
no year and are not sorted across days.

## Script contract

- Arguments: `input_file` (required path); `--csv PATH` (optional, must be a new file).
- Stdout on exit 0 or 1: the JSON object with keys `input_lines`, `parsed_lines`,
  `unparsed_lines`, `levels`, `unparsed`, `distinct_messages`, `top_messages`,
  `timeline_total`, `timeline`, `csv_path`, `csv_rows`.
- Exit 0: no ERROR or CRITICAL lines. Exit 1: at least one ERROR or CRITICAL line.
  Exit 2: usage or input error.
- Stderr on exit 2: one line of JSON, `{"error": "...", "code": "..."}`. Codes:

| Code | Meaning |
|---|---|
| USAGE | Missing or invalid arguments |
| FILE_NOT_FOUND | Input path does not exist |
| NOT_A_FILE | Input path is a folder or special file |
| FILE_UNREADABLE | Input could not be opened or read |
| TOO_LARGE | Input over 2,097,152 bytes |
| BAD_ENCODING | Input is not valid UTF-8 |
| EMPTY_INPUT | No non-blank lines |
| OUTPUT_EXISTS | CSV path already exists |
| OUTPUT_DIR_MISSING | CSV folder does not exist |
| OUTPUT_IN_INPUT_DIR | CSV folder equals the input file's folder |
| OUTPUT_WRITE_FAILED | CSV could not be written |

Unparsed reasons, as they appear in `unparsed[].reason`:

| Reason | Meaning |
|---|---|
| NO_TIMESTAMP | No ISO or syslog timestamp found (also a JSON object with no usable timestamp key) |
| NO_LEVEL | Timestamp found, but no recognized level word |
| BAD_JSON | Line starts with a brace but is not valid JSON |

## Refuse or stop when

- The input is over 2,097,152 bytes (TOO_LARGE). Ask the user for a smaller
  extract, such as one time window. Never cut the file yourself.
- The input is compressed, binary, or not UTF-8 (BAD_ENCODING). Ask the user for
  a text export.
- The CSV path already exists. Ask for a new name. Never overwrite.
- The CSV would go into the input file's folder. Ask for another folder.
- The user asks for live tailing, a cloud or remote log source, or any network
  retrieval. This skill covers local files only.
- The user asks you to redact secrets or passwords in the output. The script
  does not mask them. Say so and offer to remove lines by hand under the user's
  review; do not claim the output is safe to share.

## Files shipped

- [scripts/log_parse.py](scripts/log_parse.py): the parser and CSV writer.
- [fixtures/mixed_service.txt](fixtures/mixed_service.txt): 30-line text sample for a test run.
- [fixtures/json_lines_sample.txt](fixtures/json_lines_sample.txt): 6-line JSON-lines sample.
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
