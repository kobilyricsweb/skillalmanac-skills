# Cron Expression Explainer

## One line

Turns a five-field cron string into plain-English field descriptions and a list of the next UTC run times, using one stdlib-only Python script.

## What it does

The skill takes a five-field cron expression (minute, hour, day of month, month, day of week) and a UTC start time. A script parses each field, accepting wildcards, lists, ranges, steps and the month and weekday names JAN to DEC and SUN to SAT. It rejects anything it cannot read, such as the macro form `@daily` or a question mark, with a one-line JSON error and exit code 2.

For valid input, the script writes the normalized value set of every field, a plain-English line per field, and the next N run times after the start, where N defaults to 5 and is capped at 50. It also states which day rule applies. When both day-of-month and day-of-week are restricted, a day matches when either one matches, which is the classic Vixie behaviour. When either day field starts with an asterisk, both must match.

If an expression never fires inside the search window, for example `0 0 31 2 *`, the script reports that as a finding and exits with code 1 rather than printing an empty answer without explanation.

## When to use

Use it when someone pastes a cron string and asks what it means, when a schedule needs its next few run times checked against a calendar, or when a day-of-month and day-of-week combination is in doubt. It suits reviews of crontab lines, job configs and scheduler definitions that use the standard five-field layout.

## When not to use

Do not use it to install, edit or enable a scheduled job. It does not read crontab files, systemd timers or cloud scheduler settings. It does not handle seconds fields, year fields, the `L`, `W` or `#` extensions, or time zones other than UTC. Convert local times to UTC before you ask for run times.

## Requirements

Python 3.9 or newer. No third-party packages and no network access. The script reads one JSON input file of at most 2 MB and writes JSON to standard output. It creates no files.

## Example

Command: `python -I scripts/cron_explain.py --input fixtures/smoke.json`, where the input is `*/15 9-17 * * 1-5` from `2026-01-05T08:00Z` with count 5. Output below, verbatim, exit code 0:

```json
{
  "items": 1,
  "results": [
    {
      "index": 0,
      "expression": "*/15 9-17 * * 1-5",
      "start_utc": "2026-01-05T08:00:00Z",
      "count_requested": 5,
      "fields": {
        "minute": "0,15,30,45",
        "hour": "9,10,11,12,13,14,15,16,17",
        "day_of_month": "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31",
        "month": "1,2,3,4,5,6,7,8,9,10,11,12",
        "day_of_week": "1,2,3,4,5"
      },
      "day_rule": "and",
      "explanation": [
        "Minute: 0, 15, 30 and 45",
        "Hour: 9 through 17",
        "Day of month: every day of the month",
        "Month: every month",
        "Day of week: Monday through Friday",
        "At least one day field starts with an asterisk, so a day must match both day fields (AND)."
      ],
      "runs_utc": [
        "2026-01-05T09:00:00Z",
        "2026-01-05T09:15:00Z",
        "2026-01-05T09:30:00Z",
        "2026-01-05T09:45:00Z",
        "2026-01-05T10:00:00Z"
      ],
      "findings": []
    }
  ]
}
```

## Limits

The search covers 2928 days after the start, so a schedule that needs a leap day beyond that window will show a finding. Run times are computed in naive UTC arithmetic and never adjust for daylight saving changes, because the input is already UTC. The day rule follows the classic Vixie behaviour; other cron implementations may differ, and the script cannot check the system where the expression will run. The size limits (2 MB input, 200 characters per expression, 8 levels of JSON nesting) are working values chosen for this script.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
