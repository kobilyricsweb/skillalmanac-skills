# Listing page content: file-naming-audit

**One line:** Audits file and folder names against a naming convention and hands you a collision-checked rename plan; it never renames.

## What it does

The skill gives an agent a five-step procedure: get the names and the convention, run a read-only audit script, read collisions before anything else, write a rename plan to a file outside the tree, and report with a fixed shape. The script walks a folder (or reads a pasted listing), checks every name against a pattern such as `{date}_{project}_{asset}_v{nn}` or against a pattern inferred from the dominant existing style, and prints strict JSON. A decision table separates defects that can be fixed mechanically (spaces, case, non-ISO dates, unpadded versions) from ones that need a person (`final2`, copy suffixes, ambiguous dates, missing versions). Every proposed rename is checked against all other names, ignoring case and Unicode form, and held back if it would collide.

## Capabilities

- Case and Unicode-form collision detection, with a content hash to say whether colliding files are identical
- Convention check with 23 defect codes, including `final_FINAL2` style names, non-sortable and ambiguous dates, forbidden and risky characters, Windows reserved names, over-length paths (with a sync-prefix allowance)
- Version series report: latest by highest number, whether the newest timestamp disagrees, duplicate numbers and gaps
- Rename plan as CSV (`old,new`) that is re-verified as collision free, plus `held_back` and `needs_decision` lists
- Inference of the dominant convention, marked as needing confirmation

## When to use

You want to check or standardise the names in a shared drive or project folder, set a naming convention, clean up version tags, or find names that will break when copied between Windows, macOS and Linux.

## When not to use

Organising notes by topic (see notes-vault-organizer), restructuring a wiki (workspace-wiki-organizer), renaming files in place, editing file contents, or finding duplicates by content. It also does not build URL slugs.

## How it differs from the nearest skills

notes-vault-organizer and workspace-wiki-organizer decide where notes and pages belong; this skill checks names against a convention and builds a collision-free rename plan, and says nothing about folder structure by topic. workspace-retention-label-map labels documents by type; this one does not label anything.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent applies the defect table by hand and says so.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from saved runs of `scripts/naming_audit.py` on the fixtures in `evals/files/` and `evals/fixtures/`.

1. Convention `{date}_{project}_{asset}_v{nn}` on `evals/files/t1-agency-drive/listing.txt` (8 files, 2 folders). Exit code 1. Counts by code: `SPACE` 6, `NO_VERSION` 5, `MIXED_CASE` 4, `NO_DATE` 4, `FINAL_STYLE` 2, `AMBIGUOUS_DATE` 1, `COPY_SUFFIX` 1. The plan holds 4 rows: the folder `Client Briefs` becomes `Client-Briefs` for its three files, and `Social/2026-03-07_northwind_reel_v2.mp4` becomes `Social/2026-03-07_northwind_reel_v02.mp4`. `Social/IG post 03.04.2026.png` is not renamed: it is listed under `needs_decision` as `AMBIGUOUS_DATE`, and the two FINAL files and `Reel (1).mp4` wait for the user.
2. Convention `{name}` on `evals/fixtures/listing_collisions.txt`. Collisions: `Docs` and `docs`, and `Docs/Report.txt` and `Docs/report.txt`. The plan holds one row (`Docs/Plan.txt` to `Docs/plan.txt`); `Docs/Report.txt` and `Notes/Report Draft.txt` are in `held_back` because their new names would collide with `report.txt` and `report-draft.txt`. `plan_is_collision_free` is `true`.

## Limits

- Dates are recognised only in the documented forms; read each date change.
- The thresholds (200 characters of path, 100 of name, 50 percent for inference) are working values, not platform limits.
- Collisions are found by case and Unicode form, not similar spelling; file contents are only hashed inside collision groups.
- It audits names, not the files' contents or the links that point to them.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and all 29 script fixture checks pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review, macOS and Linux.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Point the agent at a messy client folder and state the convention.
2. The agent runs the audit: collisions first, then counts by defect code.
3. It asks which date order the numeric dates use, and re-runs.
4. It writes `plan.csv` outside the tree, shows the rows, and lists the names that need a decision.
5. The user applies the plan on a copy.

## FAQ seeds

- Will it rename my files? No. It writes a CSV plan and never renames, moves or deletes anything; you apply the plan yourself.
- Does it need network access? No.
- Does it work on a pasted list of names? Yes, with `--listing`; modified times are optional.
- Why does it hold some renames back? A rename that would produce a name already used (ignoring case) would overwrite or merge files on Windows and macOS.
- Why does it not decide the date for `03-04-2026`? It could be 3 April or 4 March; it asks, or uses `--date-order` once you say.
- Which file is the latest version? The highest number, not the newest timestamp; it tells you when the two disagree.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
