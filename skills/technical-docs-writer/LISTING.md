# Listing page content: technical-docs-writer

**One line:** Writes README, API reference, how-to and runbook pages by type, with run-before-paste code and a script that audits a docs folder.

## What it does

The skill gives an agent a fixed split of documentation into six types (README, reference, how-to, tutorial, explanation, runbook), the required sections for each, and a seven-step workflow: baseline audit, collect facts from the source, draft, run every command, add a `Last verified: <date> against <version>` line, audit again, report. Commands that cannot be run safely are labelled `Not run: <reason>` and listed in the report. A script reads a folder of Markdown files, detects each page's type, and prints strict JSON with findings. A table maps every finding to its fix and to the shortcut that would hide it.

## Capabilities

- `scripts/docs_audit.py`: per-file doc type (front matter, path or headings), missing required sections, fenced code without a language tag, unclosed fences, broken relative links and anchors (letter case checked), key-shaped secrets in file contents, missing, malformed, future or stale last-verified dates; summary counts and an `ok` flag
- Section skeletons for each type in `references/doc-types.md`
- Numeric working rules: 3 to 12 steps per how-to, first working README command within 40 lines, 90-day default staleness limit
- A fixed report: pages, what was run, what was not run, audit before and after, unknowns, owner actions

## When to use

You ask for a README, API reference, how-to, tutorial or runbook; or say the docs are stale, the examples no longer work, or tutorials and reference are mixed together; or you want a docs folder checked for broken links and old dates.

## When not to use

Docstrings and code comments, release notes, architecture decision records, generating an OpenAPI file, marketing or blog copy, and instruction files for coding agents. It does not judge whether a page is accurate; only running the commands does.

## Requirements

Python 3.9 or newer for the audit (standard library only). No network. Without Python the agent follows the section tables and checks by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill run exists yet, so there is no saved written page to show. What exists is the audit run on the saved fixtures.

1. `python scripts/docs_audit.py evals/fixtures/docs_bad --today 2026-11-21` scans 5 files and exits 1 with 17 findings (12 errors, 5 warnings): a README without Install and License sections and with an untagged code block and a link to a missing page; a how-to whose verified date is 204 days old, that has no Verify section, links to `Api.md` instead of `api.md`, and contains a key-shaped string; a runbook with no Rollback or Escalation and a verified date of 2027-01-15; a reference page with no Errors section and the verified text "sometime in spring"; a notes file with an unclosed code fence.
2. `python scripts/docs_audit.py evals/fixtures/docs_bad/runbook --today 2026-11-21` returns, among others:

```json
{"rule": "future-verified-date", "severity": "error", "line": 3,
 "message": "Verified date 2027-01-15 is in the future; record the day the commands were actually run."}
```

3. `python scripts/docs_audit.py evals/fixtures/docs_good --today 2026-11-21` scans 7 files, finds nothing and exits 0; with `--max-age-days 5` it reports 4 `stale-verified` warnings and still exits 0 (exit 1 with `--strict`).

## Limits

- The audit reads structure and text; it cannot tell whether a command is correct or a page is true.
- Type detection is a heuristic, and heading wording outside the accepted list counts as a missing section.
- Only local links and in-repo anchors are checked; external URLs are not.
- The secret check matches six common key shapes only.
- Thresholds are working values, not measured optima. Markdown only.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN; 7 of 7 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Difference from nearby skills

`agent-instruction-files` writes AGENTS.md and CLAUDE.md for coding agents, not documentation for people. `architecture-decision-records` writes decision records, which this skill treats as out of scope. `technical-seo-audit` audits public web pages; this skill audits Markdown files in a repository.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Prompt: "The README examples are broken, fix the docs folder." Agent runs the audit: 5 files, 12 errors, 5 warnings.
2. Agent runs each command in a scratch directory and pastes the real output; one block it cannot run gets `Not run: needs production access`.
3. Agent adds `Last verified: <today> against <version>` lines, fixes links, tags code blocks, and tells the owner to revoke the leaked key.
4. Audit re-run: `ok: true`; the report lists what was run and what was not.

## FAQ seeds

- Does it need network access? No.
- Does the script run my code samples? No. It never executes anything; the agent runs the samples as a workflow step, in your environment, under your permissions.
- Does it work for docs sites generated from Markdown? It audits the Markdown sources; links built by the site generator are not checked.
- Will it flag my AWS documentation example key? No; keys ending in EXAMPLE are allowed.
- How is it different from asking "write a README"? It adds a type split, required sections, a run-before-paste rule, a verified line and a folder audit. No comparison run has been done yet.
- A page is detected as the wrong type. What now? Add `doc_type: how-to` (or another type) to the page's front matter.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
