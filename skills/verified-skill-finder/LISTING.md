# Listing page content: verified-skill-finder

**One line:** Finds and compares agent skills from local folders and your own sources, scores them, and says which to trust and what is unverified.

## What it does

The skill gives an agent a six-step procedure: define the job and its must-haves, enumerate candidates, score each on a five-part rubric (fit, evidence of testing, maintenance, licence, safety), audit the leaders before any install, decide by fixed rules and report in a fixed format. A read-only script inventories skill folders (`.claude/skills`, `.agents/skills` or any path), parses each SKILL.md header, checks for `evals/`, `VERIFICATION.md`, a licence file and scripts, and ranks the skills against a query as strict JSON. Claims found in listings (install counts, badges) are kept apart from what the agent saw.

## Capabilities

- `scripts/skill_scan.py`: ranked JSON table with name, description, licence class, version, evidence files, last-modified age, keyword score, matched words, duplicates and header problems
- A rubric with numeric bands for each dimension and gates for eligibility
- A report with Seen, Claimed and Unverified sections

## When to use

You ask: is there a skill for X, which skill should I trust or install, compare these skills, what skills do I already have for this.

## When not to use

Scanning one package for malicious behaviour (use `skill-safety-audit`, which this skill calls before recommending an install), writing a new skill (`skill-authoring-and-evals`), searching the web or a marketplace. This skill never fetches a URL; for a listed URL it asks you for the downloaded folder.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent builds the table by hand (step 2 of the skill).

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved agent report. What exists is the script on the saved fixtures.

1. `python scripts/skill_scan.py --query "fill in a PDF form" evals/fixtures/claude_skills evals/fixtures/agents_skills` ranks 4 of 7 skills: `pdf-form-filler` 81.8 (MIT, evals and VERIFICATION.md present, 1 script), `pdf-toolkit` 51.5 (no licence, name differs from folder, key outside the open spec), `pdf-text-extractor` 33.3 (its own "do not use" clause excludes `fill` and `form`), `web-form-tester` 33.3.
2. `python scripts/skill_scan.py --query "clean a csv" --all evals/fixtures/claude_skills evals/fixtures/agents_skills` reports a duplicate name (`csv-cleaner` in both folders, one MIT and one GPL-3.0-only classed restrictive) and flags `notes-broken` for a missing frontmatter block.

## Limits

- The keyword score ranks words, not quality.
- Evidence and safety need judgement; the script only reports that files exist.
- Only local and user-supplied candidates are considered.
- File times change when a folder is copied.
- Scoring bands are working values, not measured against outcomes.

## Evidence

See `VERIFICATION.md`. In short: static lint result recorded there, and the 7 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Ask "is there a skill for filling PDF forms I can trust?"; the agent states the job and must-haves.
2. It runs the scan over `.claude/skills` and `.agents/skills`; four candidates appear with scores.
3. It scores the top three, runs the safety audit on the leader and marks one candidate excluded by its own "do not use" line.
4. The report shows the table, the recommendation and the Unverified list.

## FAQ seeds

- Does it search the internet or a marketplace? No. It uses folders on your machine and what you supply; URLs are listed as unscanned.
- Does it install the skill? No; it recommends and you install.
- How is it different from skill-safety-audit? That skill scans one package for risky behaviour. This one chooses among several and calls the audit for the leaders.
- Does "verified" mean safe? No. The word is used only for what the agent itself read or ran, and the report says what that was.
- Does it need network access? No.
- Will it trust install counts? No; they are recorded as claims and do not enter a score.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
