---
name: dependency-license-inventory
description: Builds an inventory of the licences that installed dependencies declare, reading only local files (node_modules package.json, site-packages dist-info METADATA, package-lock.json, go.sum, poetry.lock, Cargo.lock) with a script that lists unknown, missing, conflicting and policy-flagged licences as JSON. Use when the user asks for a dependency licence list, licence audit, open-source licence inventory, third-party notices input, or which packages are GPL or have no licence. Do not use for legal advice, compatibility rulings, vulnerability or upgrade checks, or fetching licences online.
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Dependency licence inventory

List what each installed dependency says about its own licence, group it, and mark what a person must look at. Report declarations only. Do not decide whether anything is allowed, compatible or safe to ship; that is for the user and their lawyer.

## Inputs you need

1. A folder to scan: a project root (holds `node_modules`, a virtualenv's `site-packages`, lock files, `go.sum`) or one of those folders directly.
2. The user's policy, if they have one: which licence families they accept, want reviewed, or want flagged. If they give it in words or a table, write it to a NEW file (for example `license-policy.json`) in a scratch or output location, never over a manifest, lock file or other input. If they have none, run without `--policy` and say so in the report.

Policy file shape (strict JSON; every key optional):

```json
{"buckets": {"permissive": "accept", "weak-copyleft": "review", "strong-copyleft": "flag",
             "custom": "flag", "none": "flag", "unrecognised": "review"},
 "licenses": {"ISC": "accept"},
 "packages": {"some-package": {"action": "accept", "reason": "user decision, quoted"}}}
```

Actions are `accept`, `review`, `flag`. They are the user's words; never invent a bucket action the user did not give. A package entry may be keyed `npm:name`, `pypi:name`, `go:name` or just the name.

## Workflow

```
- [ ] 1 Identify what is installed and what is only listed
- [ ] 2 Get or write the policy file
- [ ] 3 Run the scan
- [ ] 4 Read unknown[] and conflicts[] before the totals
- [ ] 5 Report
```

1. **Look first.** Check which of `node_modules`, `*.dist-info` folders, lock files and `go.sum` exist. A lock file or `go.sum` alone yields names with no declaration (go.sum has module names and hashes only), so those rows are "unknown, not installed". Say that up front; do not guess licences from memory of what a package "usually" uses.
2. **Policy.** See above. Do not accept a policy that you wrote yourself.
3. **Scan.** Run it; it reads only, makes no network call and never runs project code:

```bash
python scripts/license_inventory.py scan <project-or-folder> [<more folders>] [--policy license-policy.json] > inventory.json
python scripts/license_inventory.py normalise "MIT License" "(MIT OR Apache-2.0)"
```

   Redirect the output to a NEW file name; never to a path that is one of the scanned inputs. Exit 0: nothing needs attention. Exit 1: at least one unknown, conflict or flagged package (the normal outcome). Exit 2: usage error, unreadable policy, or no metadata found; fix what the message says.
4. **Read `unknown[]` and `conflicts[]` first**, then `summary`. Use the decision table below for each row.
5. **Report** in the fixed shape below. Run the script; do not edit it to change a result.

## Reading the result

`packages[]` rows: `ecosystem, name, version, declared` (text as found), `normalised` (SPDX-style ids, same structure), `bucket`, `expression` (OR of AND groups), `source_file`, `direct` (true, false, or null when no manifest was found for that ecosystem), `installed`, `policy_action` (null without a policy), `review_needed`, `notes`.

| Bucket | Meaning in this skill (editorial grouping, not a legal class) |
|---|---|
| permissive | MIT, Apache, BSD family, ISC, Zlib, Unlicense, CC0, public domain and similar |
| weak-copyleft | LGPL, MPL, EPL, CDDL, CC-BY-SA |
| strong-copyleft | GPL, AGPL, SSPL, EUPL |
| dual | `A OR B`: the declaration offers a choice; members are in `expression` |
| custom | `SEE LICENSE IN ...`, UNLICENSED, proprietary or commercial wording |
| unrecognised | a name the table does not know; nested parentheses; typos |
| none | nothing declared |

Rules the script applies, which you must keep: `A AND B` takes the most demanding member; `A OR B` is never resolved by you, so the policy action is the least severe alternative and the note says the project must record which one it elects; a `WITH` exception keeps its text and is shown as stated.

| Row type | What to do |
|---|---|
| `unknown` reason `no-declaration` with `detail` "resembles X" | Report "no declaration; the licence file text opens like X". Do not promote X to the declared value. |
| `unknown` reason `not-installed-no-metadata` | Report "listed in lock/go.sum, nothing local to read"; the user must install or look it up themselves. |
| `unknown` reason `custom-or-unlicensed` | Quote the declared text; a person must read the referenced file. |
| `unknown` reason `unrecognised-name` | Quote it; offer the likeliest SPDX id as a question, not a result. |
| `conflicts[]` `licence-file-differs` | Declared one thing, the file's title lines (first three non-empty lines) name another. Show both; do not pick. A text that only names another licence further down is never a conflict. |
| `mentions[]` | Info only: the file names another licence family in its body (MPL-2.0 names the GPL family as a secondary licence). Say "mentions X", never "conflict", and do not change the bucket. |
| `conflicts[]` `metadata-fields-disagree` | Python `License` field and `Classifier` lines name different licences. Show both. |
| `direct` is null for every row | No manifest was found; say direct versus transitive is unknown. |

## Report shape

```
Scanned: <folders>; ecosystems: <list>; installed rows <n>, lock-or-name-only rows <n>
Policy: <file and who supplied it, or "none supplied">
Needs a person (declared as X, review needed: yes): <table: package, version, declared, why>
No declaration or unreadable: <list from unknown[] and unreadable[]>
Declarations that disagree: <list from conflicts[]>
By bucket: <summary.by_bucket>; direct <n>, transitive <n>
Not checked: <licence compatibility; licence text past 6000 characters; anything not installed locally>
```

Never write "compliant", "safe", "approved for use" or "violates". Say "declared as", "the policy you gave marks this flag", "review needed".

## Script

`scripts/license_inventory.py`: run it. `scan` prints strict JSON (`packages`, `unknown`, `conflicts`, `unreadable`, `summary`, `statement`, `not_checked`); `normalise` shows how given strings group. Read-only: it writes nothing, so there is no output path to protect, and the fixture run proves no input file changed. Details of name mapping and file fingerprints: [references/declaration-sources.md](references/declaration-sources.md); read it when a row's `notes` or a mapping surprises you.

If Python is unavailable, do the manual fallback: for npm read the `license` field of each `node_modules/<pkg>/package.json`; for Python read `License-Expression`, then `License`, then `Classifier: License ::` lines of each `METADATA`; list packages with none of these; compare against the user's policy by hand; mark the report "manual, partial".

## Boundaries

This is an inventory of declarations, not legal advice and not a compliance statement. Never state that a combination of licences is compatible or incompatible, that distribution is permitted, or that an obligation applies. For "what does GPL require of me", say it depends on how the software is used and distributed and point them to a lawyer. Do not fetch licence text from the network or from memory to fill a gap.

## Limits

- Only declared values are read. A package can declare MIT and ship code under other terms; the script catches only a licence file that visibly opens like a different licence.
- Fingerprints cover about a dozen well-known licence openings in the first 6000 characters of one file per package; custom or modified texts return nothing.
- The bucket table is a coarse editorial grouping. Licences it does not list are `unrecognised`, not "safe".
- `direct` comes from `package.json`, `requirements*.txt` and `go.mod`. `pyproject.toml`, `Cargo.toml`, yarn and pnpm lock files are not read, so those rows show `direct` null or false by absence.
- Poetry and Cargo lock files give names and versions only; go.sum gives module names only.
- Symlinked packages (workspace links) are skipped and counted in `skipped_symlinks`.
- Dev and optional dependencies are not separated from runtime ones.
