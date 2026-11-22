# Listing page content: notes-vault-organizer

**One line:** Audits a Markdown notes vault and proposes a safe, logged move plan. It never deletes.

## What it does

The skill gives an agent an eight-step procedure for tidying an Obsidian-style vault: confirm a backup, scan, report, draft proposals, get approval by id, apply only what was approved, re-scan and compare, report. A read-only script scans the folder and prints one strict JSON document: broken and ambiguous wikilinks, orphan notes, duplicate titles and duplicate content, tag spelling variants, notes without frontmatter, and a move plan. A second command checks a move plan against the vault before anything is moved. Six safety rules (never delete, moves not copies, back up first, log every change, edits separate from moves) apply to every step.

## Capabilities

- `scripts/vault_scan.py scan`: JSON findings with file and line numbers, "did you mean" suggestions for broken links, a vault fingerprint (`tree_sha256`) that proves a scan changed nothing
- Move plan with three rules (duplicate content, stub orphans, tag-matches-folder), each move carrying a reason, a confidence and the number of path-style links it would break
- `scripts/vault_scan.py validate-plan`: rejects missing sources, taken destinations, paths leaving the vault, double moves and any action other than a move
- A change-log template with an undo step per change
- Reference notes on how links, tags and frontmatter behave, with source pages

## When to use

You say clean up my vault, organize my notes, fix broken links, merge duplicate tags, find orphan notes, or tidy my Obsidian folder, and nothing may be lost.

## When not to use

Writing or summarising notes, notes kept in an app database rather than Markdown files, cleaning a code repository, or deleting files (the skill moves to `_review/` instead and leaves deleting to you).

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the manual fallback in the skill. A backup (git commit or a copy) is required before any change.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from saved fixture runs, not from an agent session. No with-skill agent run exists yet.

1. `python scripts/vault_scan.py scan evals/fixtures/vault_messy` on a 13-note vault with 1 attachment: 4 broken links (a missing note, a missing note, a missing embedded image, a missing Markdown-linked file), 2 ambiguous links to `Ideas`, 6 orphans, 1 duplicate-title group, 1 duplicate-content group, 4 tag groups (`meeting/Meeting/meetings`, `project/Projects`, `idea/ideas`, `reading-list/reading_list`), 5 notes without frontmatter. Links and tags inside code blocks and the text `issue #42` are not counted. The proposed plan has 4 moves: `Scratch copy.md` to `_review/duplicates/`, `Quick thought.md` to `_review/stubs/`, and `Gamma.md` and `Project Alpha.md` into `Projects/`. The scan leaves the vault byte-identical (checked by the fixture runner).
2. `python scripts/vault_scan.py validate-plan evals/fixtures/vault_messy evals/fixtures/plan_bad.json`: `ok` false, 9 moves checked, 8 problems named, including `destination-exists`, `source-missing`, `unsafe-destination` (`../outside/Gamma.md`), `forbidden-action` (an attempted delete), `duplicate-source`, `not-a-note` and `duplicate-destination`. Exit code 1.

## Limits

- Heading and block parts of links are not checked.
- Links from outside the vault are invisible, so a move can break them.
- Frontmatter parsing is a small subset; nested properties are ignored.
- Tag grouping uses crude English singular rules and can miss or over-group pairs; the owner confirms every rename.
- The move rules are heuristics; the 15-word stub limit is a working value.
- Notes over 2 MB are skipped and reported.

## Difference from nearby skills

No skill in the catalogue has a folder-of-notes scope by name (only folder names were listed; no other skill's text was read). The nearest names are `taxonomy-structure-check` and `document-consistency-check`; this skill works on the links, tags, names and locations of a whole vault, and its procedure is built around not losing anything.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN, and 8 script fixture cases pass, including a read-only check on the fixture vaults. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review, real-world vaults.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Point the agent at a messy vault and ask for a cleanup; it confirms a backup and scans.
2. The report shows counts, the four broken links with line numbers, and the tag groups.
3. The agent shows a move table with ids, validates it (`ok: true`) and waits.
4. After approving two ids, the files move, the change log fills in, and a re-scan shows the same note count and no new broken links.

## FAQ seeds

- Does it need network access? No.
- Will it delete anything? No. Its rules forbid it; it moves to `_review/` instead.
- Does it work with vaults that are not Obsidian? Yes if they are folders of Markdown files; wikilinks, frontmatter tags and `#tags` are what it understands.
- Will moving notes break my links? Links by note name survive; links with a folder path do not. The plan counts them first.
- What if I only want a report? Ask for the audit only; nothing is applied until you approve ids.
- How do I undo? Every change is logged with its undo step; moves are reversed by moving back, and your backup is the last resort.
- Does any data leave my machine? The script reads files locally and prints to the terminal.

## Changelog

- 0.1.0 (2026-11-21): first draft, not yet re-verified.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; no human review has taken place.

## Behaviour notes (fix round 2026-11-21)

- Markdown links `[x](path.md)` resolve relative to the holding note first, then from the vault root, so editor-style root paths are no longer reported broken and `path_links_affected` counts them.
- A file kept by a duplicate-content rule is never also proposed for `_review/stubs`.
