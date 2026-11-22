# Listing page content: academic-paper-workflow

**One line:** Structures a paper, maps claims to your sources and checks the manuscript against your bibliography, never inventing a citation.

## What it does

The skill gives an agent a six-step procedure for an academic paper: collect the manuscript, source file and notes; pick IMRaD or a humanities argument structure; build a claim map (claim, section, key, what the source supports, status); draft with citation keys; run a checker; report. A strict rule forbids creating or completing any reference from memory: a gap becomes a `[NEEDS SOURCE]` marker and a request to the user. The checker script reads a Markdown manuscript and a BibTeX or CSL-JSON file and prints one JSON object with every finding and its line number.

## Capabilities

- `scripts/manuscript_check.py`: unresolved citation keys (with a hint for case mismatches), sources never cited, duplicate keys (case-insensitive), missing required fields per entry type, placeholder or malformed values, and numeric sentences with no citation nearby; strict JSON output and exit codes 0, 1, 2
- Reads Pandoc (`[@key]`, `@key`) and LaTeX (`\cite{}`, `\citep{}`, `\textcite{}`) citations; ignores code, comments, maths and front matter
- Claim-map table and structure guide for IMRaD and humanities essays
- A fixed report that lists what was not checked

## When to use

You say: outline my paper, structure this in IMRaD, check my citation keys, my bibliography has errors, which claims have no source, tie each claim to a source.

## When not to use

Finding new references, reformatting citation styles, LaTeX layout problems, proofreading, writing a whole assignment that must be your own, or hiding machine help from an AI-detector or plagiarism check.

How it differs from `claim-evidence-map` (same catalogue): that skill maps claims to evidence in general documents. This one is built for scholarly manuscripts: it works with BibTeX and CSL-JSON files and citation keys, checks the source records themselves, and forbids creating references.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent follows the manual check in the skill.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output of `python scripts/manuscript_check.py evals/fixtures/bad.md evals/fixtures/bad.bib` (fictional fixture data; exit code 1), abridged:

```
"ok": false,
"problems": {"unresolved_keys": 2, "uncited_sources": 3, "duplicate_keys": 1, "missing_fields": 2,
             "suspect_fields": 2, "uncited_numeric_claims": 2, "parse_errors": 0}
"unresolved_keys": [{"key": "Roe2010", "lines": [8], "hint": "differs only in letter case from 'roe2010'"},
                    {"key": "doe2018", "lines": [8]}]
"missing_fields": [{"key": "roe2010", "type": "book", "missing": ["publisher"]},
                   {"key": "lee2019", "type": "article", "missing": ["journal|journaltitle"]}]
"uncited_numeric_claims": [{"line": 8, "section": "Introduction", "numbers": ["2.5"],
                            "sentence": "Studies find a 2.5 times higher error rate in tired drivers."}, ...]
```

The same manuscript text with numbers under a Methods heading is not flagged (own data); `good.md` with `good.bib` returns `"ok": true` and exit 0.

No saved agent session exists yet, so there is no with-skill transcript to show.

## Limits

- Checks form, not truth: it cannot tell whether a source exists or says what the text claims.
- Numbers are found by digits only; spelled-out numbers and uncited claims without numbers are not found.
- Only Pandoc and common LaTeX citation forms are read.
- Required fields follow classic BibTeX types and a small CSL-JSON table.
- Sentence splitting is heuristic.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN and 8 of 8 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, cross-tool installs, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a draft and refs.bib; the user asks "check my citations, don't make anything up".
2. Run the checker: two unresolved keys, one duplicate, a book missing its publisher.
3. The agent fixes the case typo, marks the missing source `[NEEDS SOURCE]` and lists the fields the user must supply.
4. Re-run: only user-owned items remain; the report says what was not checked.

## FAQ seeds

- Will it add references for me? No. It never adds or completes a reference from memory; it tells you the gap and what to search for.
- Does it check that my sources say what I wrote? No. Only you, reading the source, can.
- Does it need network access? No.
- Does it work with LaTeX? It reads `\cite{}` style keys in a Markdown file; it does not compile LaTeX.
- Can it make my paper pass an AI detector? No, and it declines that goal.
- Does it check APA or Chicago formatting? No.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.

## Behaviour notes (fix round 2026-11-21)

- `numeric_claims_covered_by_neighbour` is now filled: every numeric sentence whose citation sits in a neighbouring sentence is listed, so the user can check by eye that the citation supports the same claim.
