# Sales call prep and follow-up

## One-line summary

Seller-side discovery call prep, and a follow-up email checked so it only promises what was said.

## What it does

Takes the notes a founder or rep pastes, builds a prep sheet and a five-stage question plan (situation, problem, impact, decision process, next step), and after the call turns the notes into a follow-up email. A standard-library script then compares the email with the notes: every promise, price, percentage, count, date and weekday in the email must be in the notes, and the next step needs a named owner and a calendar date. It also lists unanswered discovery fields and a 0-100 coverage score for the question plan. No web research is done; unknowns are marked "ask".

## Capabilities

- Prep sheet with fixed headings (goal, known, unknown, risks, proposed next step)
- 5 to 8 question plan, one or more per stage, with probes for thin answers
- Notes layout the checker reads (Markdown or JSON)
- `scripts/call_check.py`: strict JSON report, exit 0/1/2, findings with codes

## When to use / when not to

Use: first discovery calls, a recap email after a call, checking a draft follow-up for invented promises.
Not for: questions a buyer asks a vendor in a demo (a buyer-side skill such as `vendor-demo-question-set` covers that), cold outreach, researching a prospect online, CRM updates, drafting contracts or pricing.

## Requirements

Python 3.9+ standard library for the script (optional). No network. Not yet tested in any agent tool (see Evidence).

## Install

Copy the folder to `.claude/skills/sales-call-prep-and-followup/` or `.agents/skills/sales-call-prep-and-followup/`. Pinned install commands are produced at publication.

## Examples

Prompt: "Check my follow-up against my notes." (fixtures `notes_gaps.md`, `followup_bad.md`)

Real output of `python scripts/call_check.py evals/fixtures/notes_gaps.md evals/fixtures/followup_bad.md` (abridged): `ok: false`, `coverage_score: 60.0`, `unanswered_fields: ["impact", "decision_process"]`, errors `next_step_no_owner` (owner "both"), `next_step_no_date` ("next week"), `figure_not_in_notes` for Nov 30, Dec 1, 15% and 30 day, `commitment_not_in_notes` for the discount offer and the SSO promise, and `followup_missing_next_step_owner`; warnings for the words "discount" and "guarantee".

Prompt: "Is this follow-up safe to send?" (fixtures `notes_good.md`, `followup_good.md`)

Real output: `ok: true`, `coverage_score: 100.0`, no findings, next step "Demo with the dispatch lead", owner "Dana Reyes (us)", date "2026-11-19".

## Limits

Checks consistency with the notes, not truth. Promise detection is by wording and word overlap and can miss or over-flag. English only; ISO and "Nov 19" date forms. No research, no CRM, no sending. Not legal advice.

## Evidence

Script fixtures: 6/6 cases pass (see VERIFICATION.md). Trigger tests, with/without evals, cross-tool runs and human review have not been done.

## Demo script

1. Paste raw call notes with a vague next step ("next week", owner "both") and a draft email offering a 15% discount.
2. The agent runs the checker; the report shows `next_step_no_date`, `next_step_no_owner`, `figure_not_in_notes 15%`.
3. The agent asks the user for a date and owner, removes the discount, and turns the offer into a question.
4. Re-run: `ok: true`; the final email repeats the date and owner.

## FAQ seeds

- Does it need the internet? No.
- Does it research the prospect? No; only what you paste.
- How is it different from a buyer-side demo question skill? That one is for the buyer asking a vendor; this one is the seller's call and follow-up.
- Will it send the email? No.
- What if I do not use the notes layout? Paste anything; the agent rewrites it into the layout before checking.
- Does it work with a CRM export? Only as pasted text.

## Changelog

0.1.0, 2026-11-21: first draft, script fixtures run, not otherwise verified.

## License and authorship

Apache-2.0, Copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. Human full read pending.
