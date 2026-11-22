# Listing page content: email-marketing-sequences

**One line:** Plans onboarding, nurture and win-back email sequences as checked JSON that a small business can load into its sending tool.

## What it does

The skill gives an agent a seven-step procedure: collect six inputs, pick the sequence type and cadence row, write the sequence contract (trigger, one goal event, exit conditions, sender), write a contract for each email (one job, subject, preheader, one CTA), run a checker, add a deliverability checklist and a measurement plan, and report in a fixed shape. The checker (`scripts/sequence_check.py`) reads the sequence JSON and reports emails without exit conditions, gaps shorter than the minimum for the sequence type, missing sender, postal address or unsubscribe, over-long or spam-pattern subjects, duplicate CTAs, and prints a timeline. It states compliance basics for the US, EU, UK and Canada as orientation and always says to verify with counsel.

## Capabilities

- `sequence.json` in a stated schema, plus a fixed plan note
- `scripts/sequence_check.py validate`: strict JSON findings (FAIL/WARN with a code), a timeline, exit code 0/1/2, optional `--strict` and `--min-gap`
- Playbooks with a cadence table for onboarding, nurture and win-back, and sunset rules
- A consent decision table and a header/footer checklist
- A deliverability checklist, a measurement plan with a holdout design, and guardrail numbers

## When to use

You ask for a drip campaign, welcome series, onboarding or lifecycle flow, nurture sequence, or win-back series, or want an existing sequence audited for exits, cadence, unsubscribe, subject lines and repeated CTAs.

## When not to use

One-to-one replies and inbox triage (that is `email-writing-and-triage`), HTML template design (that is `html-email-design`), one-off newsletters, DNS authentication setup, and sending to purchased, rented or scraped lists, which the skill declines to design for.

## Requirements

Python 3.9 or newer for the checker (standard library only). No network. Without Python the agent walks the check table in `references/sequence_schema.md` by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

From saved fixture runs of the checker (`python evals/run_fixtures.py`, 8 of 8 cases pass):

1. `python scripts/sequence_check.py validate evals/fixtures/good_onboarding.json` gives `ok: true`, 5 emails, 0 fail, 0 warn, and the timeline days 0, 2, 5, 9, 14 with gaps 2, 3, 4 and 5 days.
2. `python scripts/sequence_check.py validate evals/fixtures/bad_winback.json` gives `ok: false`, 13 fail and 16 warn, exit code 1. Examples: `consent-basis-unacceptable` (purchased list), `subject-fake-reply` (`Re: your order - ACT NOW!!`), `unsubscribe-missing`, `exit-missing`, `gap-too-short` (one day after the previous email on a 3-day minimum), `subject-too-long`, `cta-duplicate-label`.
3. `python scripts/sequence_check.py validate evals/fixtures/nurture_warnings_only.json --strict` exits 1 on five warnings; without `--strict` it exits 0.

No with-skill agent run exists yet, so there is no saved sequence or plan note to show.

## Limits

- The checker reads a JSON description, not the real emails, bodies, images or footers.
- Spam-trigger matching is a short English phrase list; filters weigh reputation and engagement far more.
- Cadence minimums and subject limits are working values, not measured optima.
- Compliance notes are orientation, not legal advice; verify with counsel.
- It does not choose a platform, build templates or send anything.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL after the evidence files were added, 8 fixture cases pass with expected values worked out by hand. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool installs, human review.

## Difference from neighbouring skills

`email-writing-and-triage` handles single messages to a person. `html-email-design` designs templates and markup. This skill designs the automated series around them: when each email is sent, what stops it, what it asks for, and whether it is allowed to send at all.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a short brief for a plant shop; the agent asks for the sender address and how people joined the list.
2. The agent drafts `sequence.json` with five emails and a timeline.
3. The checker flags a too-short gap and a missing preheader; the agent fixes both and re-runs to `ok: true`.
4. The agent shows the plan note: consent basis, guardrails, holdout, and the list of placeholders still to replace.

## FAQ seeds

1. Does it send the emails? No; it plans and checks the sequence, and you load it into your sending tool.
2. Does it need network access? No.
3. Is this legal advice? No; it states basics and says to verify with counsel.
4. Can it write to a list I bought? No; it declines and suggests lawful ways to get consent.
5. Why not report open rates? Mail privacy features inflate opens; the plan uses goal events, clicks, replies and a holdout.
6. How is it different from the email-writing skill? That one writes single emails; this one designs the whole automated series.
7. What data leaves my machine? None from the skill; the checker reads one local file and prints to the terminal.
8. How do I uninstall it? Delete the skill folder.

## Changelog

- 0.1.0 (2026-11-21): first draft, static lint and fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings. Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
