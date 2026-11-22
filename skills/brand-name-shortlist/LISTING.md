# Listing page content: brand-name-shortlist

**One line:** Generates candidate names and screens them by spelling, sound and collisions into a shortlist of 5.

## What it does

The skill walks an agent through a naming brief, 30 to 60 candidates across five name types (descriptive, invented, compound, metaphor, acronym), a scripted screen, a say-it-and-type-it test and a shortlist of 5 with a reason for each. The script scores length, syllables, consonant and vowel runs, ambiguous spellings, doubled letters, near-duplicates inside the list, collisions with a competitor list, words from an avoid list, a short bundled unwanted-string list and how the name reads when joined to a suffix such as .com. It prints strict JSON and builds handle and domain-style slugs offline. It never checks availability and never says a name is clear of trademark conflict; it lists what the user must verify.

## Capabilities

- `scripts/score_names.py`: ranking with `score`, `verdict` (keep, review, cut) and `flags[]`; shortlist with reasons, watch items and a to-verify list; near-duplicate pairs; slugs
- A decision table of name types with strengths and risks, and the spelling and pronunciation tests
- A fixed report: brief assumptions, shortlist with reasons, to-verify list, what was not checked

## When to use

You say name my startup, business name ideas, brand name generator, or help me pick between these names, and you want names filtered by something measurable.

## When not to use

Logos and marks (see logo-and-mark-design), guidelines for an existing brand (brand-guidelines-kit), taglines, campaign plans, checking whether a domain or trademark is free, or naming things in code. Difference: this skill ranks candidate names by spelling, sound and collision tests ahead of any visual work.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent applies the thresholds table by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved conversation to show. What exists is the script on the saved fixtures:

1. `python scripts/score_names.py evals/fixtures/candidates_mixed.txt --competitors evals/fixtures/competitors.txt --avoid evals/fixtures/avoid.txt`: 20 candidates; shortlist Budgetr (100), Fynex (100), Nestegg (97), Pennywise (97), Coinfield (92). Monetra is cut as identical to a competitor; Spendsmart is cut for a four-consonant run and for containing "spend" from the avoid list; Ledgerly and Ledgerlee, and Tallybird and Tallybud, are reported as near-duplicates (edit distance 2). A sixth strong name, Moneyfy, is held out by the two-per-type cap.
2. `python scripts/score_names.py evals/fixtures/candidates_few.txt --suffix .io --top 3`: exit 1 and `shortlist_shortfall: true`; Xqzt and Brkstnd are cut (no vowel), "Penny wise" is cut as the same letters as Pennywise, and its domain slug is `pennywise.io`.

## Limits

- Syllable and cluster rules are heuristics for English-looking words; invented words can be mis-scored.
- The bundled unwanted-string list is short and not exhaustive; supply an avoid list and ask native speakers.
- Edit distance catches names that look alike, not names that sound alike.
- No availability or trademark check of any kind; a high score is not clearance.
- Score weights are working values, not measured against naming outcomes.

## Evidence

See `VERIFICATION.md`. In short: static lint passed, and the 3 script fixture cases pass with expected values worked out by hand. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a naming brief and 20 drafted names; the agent saves the three input files.
2. Run the script: two names cut (competitor match, avoid word), two near-duplicate pairs reported.
3. The agent applies the say-it-and-type-it test and swaps one name with a stated reason.
4. The reply shows the shortlist of 5, the to-verify list (domains in slug form, trademark search, handles) and the Not checked line.

## FAQ seeds

- Will it tell me the name is free to use? No. It has no network and the skill forbids claiming availability or trademark safety.
- Does it work for names in other languages? The scoring is English-oriented; supply an avoid list and ask a native speaker.
- Does it need network access? No.
- How is it different from asking a model for name ideas? It adds a screen with fixed thresholds, a collision check against your competitors and a fixed report. No comparison run has been done yet.
- How is it different from logo-and-mark-design? That skill is about the visual mark; this one only chooses the name.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
