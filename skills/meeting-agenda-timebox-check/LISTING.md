# Listing page content: meeting-agenda-timebox-check

**One line:** Checks a meeting agenda against its time slot and flags items with no owner, outcome or decision question.

## What it does

The skill walks an agent through collecting the meeting facts and one outcome per item, writing the agenda in a small markdown or JSON layout, and running a script on it. The script chains the item times from the start, adds them up against the slot with a 10 percent buffer, and applies fixed rules: time ceilings per goal type, a decision question on every decide item, no decision in the last 10 percent, a break above 90 minutes, no owner above 50 percent of item minutes, and purpose-specific structure for decide and brainstorm meetings. When the buffer is short it proposes cuts in a fixed order and never cuts a decision. The agent then fixes the flags and reports in a fixed shape.

## Capabilities

- `scripts/check_agenda.py`: strict JSON report with item start and end times, flags per item, findings by severity, suggested cuts, attendee-hours (only from a user-supplied count) and a verdict
- Exit codes 0 pass, 1 warn or fail, 2 bad input; optional `--out` that refuses to overwrite the agenda
- A flag-and-fix table in `references/flags-and-fixes.md`
- A fixed final report that lists what was accepted and what was not checked

## When to use

You say check my agenda, will this fit in 30 minutes, is this meeting overbooked, timebox this agenda, or you paste items with minutes.

## When not to use

Notes, minutes or action items after the meeting (use a notes-and-actions skill such as `meeting-notes-and-actions`), finding a free slot, writing or sending invites, calendar changes. This skill works before the meeting and on one agenda file.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent applies the decision tables by hand and says the arithmetic was not script-checked.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet. What exists is the script on saved fixtures:

1. `python scripts/check_agenda.py evals/fixtures/tight_buffer.md`: a 30 minute slot with 28 minutes booked. Verdict `warn`, exit 1, one finding `BUFFER_TOO_SMALL` ("2 min free, at least 3 min (10 percent) wanted"), suggested cut: trim item 3 from 8 to 5 minutes, saving 3.
2. `python scripts/check_agenda.py evals/fixtures/bad_overbooked.md`: 65 minutes in a 60 minute slot. Verdict `fail`, exit 1; flags include `OVERBOOKED`, `NO_DECISION_QUESTION` on the pricing item, `NO_OWNER` and `NO_OUTCOME` on two items, `DECISION_LATE` on the last item, `OWNER_DOMINANT` for one owner with 45 of 65 minutes; suggested cut: move item 1 (marked "no discussion needed") to a pre-read, saving 20 minutes; attendee-hours 8.0 for the slot against 8.67 booked.

## Limits

- Thresholds are working values, not measured optima.
- The outcome check looks at wording only (question mark, result verb).
- Owner share counts scheduled minutes, not who speaks.
- Clock times assume one continuous block; no time zones.
- Attendee-hours need a count from the user.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and 14 script fixture cases pass against expected values worked out by hand. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a 30 minute agenda with four topics; the agent asks for the missing outcomes and owners.
2. Run the check: verdict fail, 35 minutes booked, one item marked "no discussion needed".
3. The agent moves that item to a pre-read, rewrites the decision as a question, and re-runs: pass.
4. Show the final report, including attendee-hours and what was not checked.

## FAQ seeds

- Does it send invites or touch my calendar? No; it reads one file and prints a report.
- How is it different from meeting-notes-and-actions? That skill works on what happened after the meeting; this one checks the agenda before it.
- Where do the 10 and 15 minute limits come from? They are house working values; accept a warning when your group knows better.
- Does it need network access? No.
- Does it know how many people attend? Only if you tell it; otherwise attendee-hours are reported as not computed.
- Will it cut my decision item? Never; it moves decisions earlier instead.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
