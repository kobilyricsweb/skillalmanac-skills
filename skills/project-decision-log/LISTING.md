# project-decision-log

## One line

Keeps a DECISIONS.md file of numbered project decisions, each with its context, the options weighed, the reason, the consequences and a revisit date, and records a change of mind as a new superseding entry.

## What it does

The skill gives an agent a fixed procedure for a single file at the project root. Before acting on a topic, the agent reads the active entries. When a decision meets a short threshold test (hard to undo, costly, or contested), the agent assigns the next id, fills a ten-line template, appends the entry and runs a consistency check. If a new decision replaces an old one, the old entry's Status line is the only line that changes, so the history of what was believed and when stays readable. The reply to the user uses five fixed headings so the outcome can be scanned at a glance.

## When to use

Use it when a choice will cost real time to reverse, when two people or sources disagreed, or when a future session is likely to ask why something was built a certain way. It suits small teams that keep their working notes in a repository and want the reasoning to travel with the code.

## When not to use

Do not use it for meeting minutes, task lists, bug tracking, or personal journals. Routine formatting and naming choices inside one file do not qualify under the threshold table. The skill does not decide anything on its own; it records decisions a person has made.

## Requirements

A text-capable agent with file read and write access to the project folder. No scripts, no network access and no installed software beyond the agent itself.

## Example

The smoke run in VERIFICATION.md logs three decisions and then supersedes the first one with a fourth. The resulting DECISIONS.md shows the status line of the superseded entry changed from active to superseded by D-004, while its body text is unchanged. The reply headings for the fourth entry read: Read with three entries and highest id D-003, Logged with D-004 superseding D-001, Changed with D-001 moving from active to superseded, Open questions as none, and Check as pass.

## Limits

The working thresholds (one working day, 90-day default revisit) are working values chosen for this procedure, not industry standards. The skill assumes one DECISIONS.md per project and one writer at a time; concurrent edits are not handled. It does not repair malformed files and stops instead. It does not check whether the recorded decision is correct, only that the record is complete and consistent.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
