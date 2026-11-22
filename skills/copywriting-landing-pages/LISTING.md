# Listing page content: copywriting-landing-pages

**One line:** Writes and audits landing-page copy: five fixed sections, every number sourced, no hype.

## What it does

The skill gives an agent a section contract for a landing page (hero promise, proof, how it works, objections, CTA) with word limits per block and a one-message-per-section rule. It adds a claim rule: every number carries a source in the same sentence, or it is removed, and "thousands of" counts as a number. It defines CTA grammar (verb plus object, one destination, at most two wordings) and a banned-phrase list. A script audits a Markdown or HTML draft and prints strict JSON: section presence and order, hero length, block limits, unsupported numeric claims, banned phrases, CTA count and consistency, and a reading-grade proxy.

## Capabilities

- `scripts/lp_audit.py`: strict-JSON audit with severity per finding and exit codes 0, 1 or 2
- A five-input intake (visitor, action, outcome, proof, objections) before any writing
- A fixed report: sources used, claims removed or marked NEEDED, what was not checked
- `references/rules.md`: thresholds with reasons, accepted source patterns, banned phrases with replacements

## When to use

You ask for landing page or homepage copy, a hero headline, a signup or waitlist page, or a rewrite of a page that is full of hype or unsourced statistics. You have a draft and want it checked before it ships.

## When not to use

Campaign briefs and channel plans (see the campaign-brief skill, which plans the campaign; this one writes the page), ad copy, email sequences, keyword research, product descriptions for a catalogue, page design or performance work.

## How it differs from nearby skills

- `marketing-campaign-brief` plans objective, audience, channels and budget; it does not write page copy. This skill writes and audits the page itself.
- `claim-evidence-map` maps claims to evidence in any document; this skill applies the same discipline inside a fixed page structure, with CTA and length rules, and checks it by script.
- `promotion-variant-check` compares promotion variants; this skill audits one landing-page draft.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent applies the self-check by hand and reports "audit not run".

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved agent-written page. What exists is the audit on saved fixtures:

1. `python scripts/lp_audit.py evals/files/t3-audit-html/page.html` gives `verdict: fix`, 2 errors: `cta-destination-split` (hero goes to `.../ledgerly/start`, final CTA to `.../ledgerly/demo`) and `unsupported-number` on line 8 ("cut month-end close from 6 days to 2 for 48 small firms in 2026"). Exit code 1.
2. `python scripts/lp_audit.py evals/fixtures/bad.md` gives `verdict: fix`, 10 errors and 22 warnings, 14-word headline, grade 14.7, and flags "thousands of", "the best", "guaranteed results", "#1", "10 hours a week", "300%", three missing sections and four different CTA destinations.
3. `python scripts/lp_audit.py evals/fixtures/t2_reference_page.md` gives `verdict: pass`, 0 errors, 0 warnings, grade 3.4. This page was written by hand by the skill author as a reference for task 2, not by an agent run.

## Limits

- The script checks structure and surface patterns; it cannot verify that a source is real or says what the copy claims.
- Section roles are inferred from heading words.
- Claims written in words ("twice as fast") are not detected.
- Thresholds are working values, not tuned on conversion data; the skill does not predict conversion.
- English only.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and 15 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a hype-heavy draft and a short fact sheet; the agent runs the audit: `fix`, unsupported numbers and banned phrases listed by line.
2. The agent rewrites into the five sections, keeps only the sourced figures, marks the rest as removed.
3. Re-run: `pass`, hero 7 words, one CTA destination.
4. The report lists sources used, claims removed and what was not checked.

## FAQ seeds

- Will it invent statistics or testimonials? No; the rule is source or remove, and it asks for missing proof or writes a `[NEEDED]` placeholder.
- Does it need network access? No.
- Does it work on HTML exported from a page builder? Yes for the visible text structure; scripts, styles and head content are ignored; it does not render the page.
- Will it make my page convert? It checks the page against a contract; conversion is measured only by testing the live page.
- Can I leave out the FAQ or proof section? Yes, pass `--optional proof,objections` and the report states what is missing.
- Why does it flag "Learn more"? Vague labels do not say what happens next; the CTA rule asks for a verb and an object.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet. Accountable editor: Global Media Holdings.
