# Listing page content: plain-language-readability

**One line:** Rewrites public and customer text to a target reading level, measuring the change and checking that numbers and links survive.

## What it does

The skill gives an agent a fixed procedure for plain-language rewriting: collect the audience and target, measure the original, plan moves per finding, rewrite, compare, read both versions side by side, and report. A script (`scripts/readability.py`) counts words, sentences and syllables with a documented heuristic and prints Flesch reading ease, Flesch-Kincaid grade, average sentence length, a list of long sentences, passive-voice candidates (with whether an actor is named), uncommon words with plain suggestions, wordy phrases, and the status of a jargon list the user supplies. Given a rewrite, it adds a before-and-after table and verifies that every number and link in the original is still there; it also lists changes in must, may, should and will, in negations and in conditions for the agent to confirm. A preserve-facts rule forbids changing meaning.

## Capabilities

- `scripts/readability.py TEXT`: strict JSON with scores, findings and a low-reliability flag for samples under 100 words
- `--rewrite FILE`: before and after metrics, `numbers_preserved`, link check, modal, negation and condition warnings
- `--jargon FILE`: replace-list and keep-list (`!term`) with a gloss check
- `--grade N`: pass or fail against a target grade (exit code 1 when missed)
- Decision tables for starting targets by audience, rewrite moves per finding, a modal-verb table and a stop rule
- A fixed report: target, before and after figures, facts, what was kept on purpose, what is left for the author, what was not checked

## When to use

You say plain language, plain English, simplify this notice, lower the reading level, make it grade 6, easier to read, or give me a readability score, for public notices, benefits letters, customer-support replies, lesson text or staff guidance.

## When not to use

Removing AI-sounding style (use natural-prose-editor), translation, summarising, legal or medical sign-off, accessibility certification, or getting text past AI-detector or plagiarism checks (the skill declines that goal). How it differs from natural-prose-editor: that skill edits style and measures patterns without a reading level; this one measures readability against a target and verifies that meaning-critical numbers, links and obligation words survive the rewrite.

## Requirements

Python 3.9 or newer for the script (standard library only). No network, no subprocess. Without Python the agent follows the manual-count fallback in `SKILL.md`. English text only.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved rewrite by an agent. What exists is the script on saved fixtures:

1. `python scripts/readability.py evals/fixtures/notice_original.md --grade 8`: 144 words, 7 sentences; Flesch reading ease 52.0 (fairly difficult), Flesch-Kincaid grade 11.1; 3 sentences over 25 words; 8 passive candidates in 4 of 7 sentences (57%); exit code 1 because grade 11.1 is above 8.
2. `python scripts/readability.py evals/fixtures/notice_original.md --rewrite evals/fixtures/notice_good.md --jargon evals/fixtures/jargon.txt --grade 8`: grade 11.1 to 4.0, ease 52.0 to 87.4, average sentence 20.6 to 11.9 words, long sentences 3 to 0, `numbers_preserved` true, links unchanged, exit code 0. Warnings: `can` 1 to 0, `must` 3 to 2, one more negation, the name "Department" missing, all for the agent to confirm. The kept term "hearing" is reported `kept_no_gloss`.
3. The same original against `notice_bad.md` (a rewrite written to fail): `numbers_preserved` false (14 missing, 10 added), the e-mail address missing, exit code 1.

## Limits

- English only; the formulas count sentence and word length, not how hard the ideas are.
- Syllable counting is a heuristic and the common-word list is small; the passive check misses some passives and flags some adjectives.
- Under 100 words the figures are unstable.
- No score proves that readers understand the text or that it meets a legal standard.
- Starting targets by audience are working values from common practice, not standards.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 16 script fixture cases pass (including refusals to overwrite an input). Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review, accuracy of the heuristics on a real corpus.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a dense public notice; the agent saves it and runs the script: grade 11.1, three long sentences, eight passive candidates.
2. The agent lists its moves per finding and the terms that must stay.
3. The rewrite is compared: grade 4.0, numbers preserved, links unchanged, modal warnings listed.
4. The agent reads both versions side by side, confirms each warning, and prints the report, ending with "Not checked: comprehension by real readers".

## FAQ seeds

1. Does it need network access? No.
2. Does it work for languages other than English? No; the script refuses to score text it detects as non-English.
3. Will a lower grade mean readers understand it? Not necessarily; the report says what was and was not checked.
4. What if my text has headings and lists? They are left out of sentence statistics and still checked for numbers, links and jargon.
5. Can it change "may" to "must"? It flags any change in modal verbs; the agent must confirm each against the source.
6. How is it different from natural-prose-editor? See "When not to use".
7. Does the script change my files? No; it writes only a JSON report if you pass `--out`, and never over an input.
8. How do I uninstall it? Delete the skill folder.

## Changelog

- 0.1.0 (2026-11-21): first draft. Static lint and script fixtures only; not re-verified in any tool.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5 under the Skill Almanac Editorial name; the accountable editor is Global Media Holdings. No human review has taken place yet.
