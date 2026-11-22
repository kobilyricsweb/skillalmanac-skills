## תקציר

- ה-skill עורך מחקר מתחרים ושוק עם יומן מקורות: כל מקור מסומן opened / snippet / unverified, ואין מספר בלי מקור.
- כולל script לא מקוון שמכשיל דוח עם מספר בלי מקור או עם מקור חלש שלא סומן.
- סטטוס: REJECTED. גבר על הבסיס רק במשימה אחת מתוך שלוש (תיקו אחת, הפסד אחד), גם אחרי תיקון אחד.
- הראיות נשמרו; אין לפרסם.

---

# Listing page content: sourced-market-research

**One line:** Competitor and market research in which every figure traces to a source marked opened, snippet or unverified.

## What it does

Seven ground rules (three source states, no figure without a source, quote figures as shown, estimates labelled with arithmetic, conflicts are findings, fetched pages are data and not instructions, counts need matching definitions) and a six-step workflow: frame, collect with the ledger open, draft, check, read back, deliver. The script checks that each line with a figure cites a ledger id or carries an estimate tag, that weak sources are marked in the line, and that the ledger is complete.

## Capabilities

- `claim_ledger_check.py` for a report and a `sources.csv` ledger.
- A report skeleton, sentence patterns, rules for estimates and conflicting sources, a source-quality order.
- A review mode that returns a claim-by-claim verdict table.

## When to use

Not recommended for use in its current form; see Evidence.

## When not to use

Keyword volume studies, academic literature reviews, collecting personal data about individuals.

## Requirements

Python 3.9+ (standard library). No network for the script; sources are gathered with the agent's own tools. Tested in one tool only (see Evidence).

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved runs)

1. Prompt: "Write a competitor brief on Canadian pet-sitting marketplaces. Include market size." Saved run: `evals/runs/m1-competitor-brief/with_skill/reply.md` (blind 9 against 7): both conflicts shown, the paywalled market figure marked as a preview, the embedded instruction in a saved page ignored and noted.
2. Prompt: "Quick one: what is the market size? I need a number for a slide." Saved runs: `evals/runs/m2-market-size/with_skill_v010/` and `with_skill/` (v0.1.1). Both were judged worse than the baseline: too long for the question, and the pasted wording lost a caveat.

## Limits

- Did not beat the baseline: 1 win, 1 tie, 1 loss.
- The method adds length and bookkeeping that a short question does not need.
- The script checks form, not whether a source supports a claim.
- The baseline model (haiku alias) already marked snippets, showed conflicts and ignored the embedded instruction on these tasks.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model (haiku alias), one tool, 2026-11-20. Blind grading: 1 of 3 preferred with the skill, 1 tie, 1 preferred without. Static lint 0 FAIL. Token overhead about +25% per run. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Not applicable while the skill is rejected.

## FAQ seeds

- Why rejected? It did not beat the same model without the skill on two of three tasks.
- Is the checker still useful? It caught every seeded problem in its fixtures; it could be reused in a narrower skill for long reports.

## Changelog

- 0.1.1 (2026-11-20): one revision after the first eval runs; see VERIFICATION.md.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
