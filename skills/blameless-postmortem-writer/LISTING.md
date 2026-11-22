# blameless-postmortem-writer

## One line

Turns raw responder notes and a timeline for one resolved incident into a postmortem with a fixed heading set, UTC timing math, system-and-process contributing factors and action items that each have a checkable done-condition.

## What it does

The skill takes the notes an incident responder left behind, which are usually a chat log, a few timestamps and some remarks, and produces one Markdown postmortem. It normalises every timeline entry to UTC, computes detection, mitigation and resolution durations from those timestamps only, and maps the impact to a severity label using the criteria the user supplies. Contributing factors are sorted into System, Process and Environment and written as mechanisms, so a reader sees what the system allowed rather than who acted. Each action item carries a type, an owner that is a team or role, a due date from fixed windows (14, 30, 45 and 60 days) and a done-condition that names something a reviewer can inspect. A final blame pass rewrites any sentence that treats a person as the cause, and the author notes list every field the notes did not supply.

## When to use

Use it after an incident has been resolved and the notes are still fresh. It fits a team that has a rough timeline in a chat export and needs a document that the next reader can act on, or an existing draft whose action items say things like "improve alerting" and need concrete checks.

## When not to use

Do not use it during a live outage, where the output would be a status update rather than a postmortem. It does not perform forensics for a security breach, and it does not produce legal or regulatory filings. It will not invent timestamps, impact counts or severity, so a request that depends on figures the notes do not contain will come back with "not provided" entries and questions.

## Requirements

Any text-capable agent that can follow a Markdown skill. No scripts, no network access and no extra tools. The user needs to supply the notes, the time offset if the notes are not in UTC, and any severity criteria they want applied.

## Example

Excerpt from the postmortem produced by the smoke run (fictional 47-minute checkout outage, notes in the fixtures folder):

```
## Metadata

| Field | Value |
|---|---|
| Impact start (UTC) | 14:05 |
| Detected (UTC) | 14:09 |
| Mitigated (UTC) | 14:33 |
| Resolved (UTC) | 14:52 |
| Duration (min) | 47 |
| Time to detect (min) | 4 |
| Time to mitigate (min) | 24 |
```

## Limits

The due-date windows and the 15-minute timeline gap are working values chosen for this skill, not published standards, and teams should change them to suit their own review cycle. The skill cannot judge whether a severity label is correct when the user's criteria are ambiguous; it flags the ambiguity in the author notes instead. It writes one document per incident and does not merge several incidents into a trend report. Output quality depends on the notes: a sparse log gives a thin timeline and fewer contributing factors, and the skill stops rather than filling the gap.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
