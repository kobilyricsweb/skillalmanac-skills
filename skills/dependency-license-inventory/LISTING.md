# Dependency licence inventory

## One-line summary

Lists the licences your installed dependencies declare, from local files only, and marks what needs a human look.

## What it does

A script walks a project folder, `node_modules`, or a virtualenv's `site-packages` and reads each package's own declaration: the `license` field of `package.json`, or `License-Expression`, `License` and `Classifier` lines of `METADATA`. It also uses `package-lock.json`, `poetry.lock`, `Cargo.lock` and `go.sum` for names, so packages that are listed but not installed show up as "unknown" instead of being guessed. Declared names are normalised to SPDX-style ids and grouped (permissive, weak copyleft, strong copyleft, dual, custom, unrecognised, none). If you supply a policy table, each package also gets your action (accept, review, flag). It reports a licence file whose opening text looks like a different licence than the declared one. Output is strict JSON.

## Capabilities

- Inventory of declared licences with direct versus transitive split (npm `package.json`, `requirements*.txt`, `go.mod` as manifests)
- `unknown[]`: no declaration, custom text, unrecognised name, not installed
- `conflicts[]`: licence file versus declaration, Python `License` versus `Classifier`
- Policy table from the user applied per bucket, per licence id and per package
- A `normalise` mode to see how any licence string is read
- Fixed hand-off report: "declared as X, review needed: yes or no"

## When to use / when not to

Use for a licence list before a customer questionnaire, a due-diligence request, a notices file, or an internal review.

Not for: legal advice or compatibility rulings; vulnerability scans; upgrade impact (see `dependency-upgrade-impact-map`); looking up library documentation (see `library-docs-lookup`); SBOM formats with hashes and purls; licence text from the network. Difference from the neighbours: those map upgrades or fetch docs; this one only reads what is installed locally and says what each package declares about itself.

## Requirements

Python 3.9 or newer, standard library only. Network: none. Tested on Windows 11 with Python 3.11 only.

## Install

Copy the folder to `.claude/skills/dependency-license-inventory/` or `.agents/skills/dependency-license-inventory/`. Pin to the published tag when one exists.

## Examples

Prompt: "Give me a licence inventory for our lawyer. MIT, Apache and BSD are fine, LGPL and MPL need a look, GPL or no licence gets flagged."

Real output of `python scripts/license_inventory.py scan evals/fixtures/bad_project --policy evals/fixtures/bad_project/policy.json` (fictional fixture packages), trimmed:

```
summary: packages 18, direct 7, transitive 11, unknown 8, conflicts 2, flagged 9, review_needed 10
by_bucket: custom 1, dual 2, none 6, permissive 5, strong-copyleft 2, unrecognised 1, weak-copyleft 1
unknown: delta-tool  no-declaration (licence file text resembles MIT)
         zeta-core   custom-or-unlicensed ("SEE LICENSE IN LICENSE.txt")
         theta-wild  unrecognised-name ("Wild Public Thing 1")
         example.test/dep-a  not-installed-no-metadata (go.sum names only)
conflicts: epsilon-util  declared MIT, licence file text resembles Apache-2.0
           pygamma       License "GPLv3+" versus Classifier "MIT License"
pygamma: declared "GPLv3+" -> GPL-3.0-or-later, strong-copyleft, policy_action flag
```

Prompt: "I only have lock files, what are the licences?" Output (`evals/files/t3-lock-only`): three of four packages are `not-installed-no-metadata`; the fourth (`semver-like`) shows `ISC` read from the lock file, `installed: false`. The skill does not fill the others from memory.

## Limits

Declared values only; a package can declare MIT and ship other terms. Licence-file hints cover about a dozen well-known openings in the first 6000 characters of one file. Bucket table is an editorial grouping, not a legal class. `pyproject.toml`, `Cargo.toml`, yarn and pnpm lock files are not read for direct dependencies. Symlinked workspace packages are skipped. No compatibility or compliance statement is ever made.

## Evidence

Static lint and script fixtures only. Task evals, trigger tests, cross-tool runs and human review have not been done; see VERIFICATION.md. Not publishable yet.

## Demo script (60 to 90 seconds)

1. Prompt: "Inventory the licences in this repo; here is our policy."
2. The agent runs `scan`; beat 1 shows 18 packages, 8 unknown.
3. Beat 2 shows `delta-tool`: no declaration, file opens like MIT, reported as unknown, not as MIT.
4. Beat 3 shows the `epsilon-util` conflict and `pygamma` GPL flag.
5. Result: a table "declared as X, review needed: yes/no", with a "Not checked" line and no legal verdict.

## FAQ seeds

- Does it need network? No; it reads local files only.
- Why are lock-file packages "unknown"? Lock files and go.sum rarely hold licences; the skill will not guess.
- Does it tell me if I can ship GPL code? No, it never gives compatibility or legal conclusions.
- Who decides what is acceptable? You, through the policy table; the skill applies it and records it.
- What about dual-licensed packages? Shown as `dual` with each alternative; the policy action is the least severe alternative and the project must record which is elected.
- How is it different from an SBOM tool? It produces a review list from declarations, not a signed bill of materials.
- Does it change my files? No; the fixture run hashes all inputs before and after.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft; static lint and script fixtures only.

## License and authorship

Apache-2.0. Copyright 2026 Global Media Holdings (skillalmanac.com). Drafted with AI assistance (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has taken place yet.
