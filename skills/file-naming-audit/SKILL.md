---
name: file-naming-audit
description: Audits the file and folder names of a shared drive or project tree against a naming convention (date prefix, case, separators, zero-padded version tags, forbidden characters, path length), finds names that differ only in case, and writes a collision-checked rename plan as a dry run, never renaming anything. Use when the user asks to check, standardise or clean up file names, set a naming convention, fix final_FINAL2 style versions, or find names that break on Windows or macOS. Do not use for organising notes by topic, renaming files in place, editing file contents or finding duplicates by content.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only, no network. Without Python, follow the manual fallback below.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# File naming audit

Check names against one convention, report every break, and hand the user a rename plan they run themselves. This skill and its script never rename, move or delete anything.

## Convention syntax

The script takes the convention as a pattern. Literal text must be lower case.

| Placeholder | Matches |
|---|---|
| `{date}` | ISO date `2026-03-04`, calendar-valid |
| `{date8}` | compact date `20260304` |
| `{nn}` / `{nnn}` | zero-padded number of that width; the literal right before it must end in `v`, as in `_v{nn}` |
| `{anything_else}` | a field of letters and digits; words inside a field are joined with `-`, fields are separated by the literal between placeholders (`_` is the house default) |

Example: `{date}_{project}_{asset}_v{nn}` accepts `2026-03-04_northwind_homepage-hero_v02.psd`. The extension is checked separately and must be lower case. The script cannot split an unstructured name such as `Homepage Hero Final` into `{project}` and `{asset}`; it reports those names for a human decision instead of guessing.

## Procedure

```
- [ ] 1 Get the names and the convention
- [ ] 2 Run the audit
- [ ] 3 Read collisions first, then the rest
- [ ] 4 Write the plan outside the tree
- [ ] 5 Report
```

1. **Names.** Use the folder path. If the user pastes names, save them one relative path per line in a file and pass `--listing`; add a TAB and an ISO time after a path to supply its modified time. Listing lines are trimmed, so names with leading or trailing spaces can only be found by walking a real folder. **Convention.** Use the user's, translated into the pattern above. If they have none, run without `--convention`: the script infers the dominant pattern and sets `needs_confirmation: true`. Show the inferred pattern and its `evidence` and get a yes before treating `NO_DATE` or `NO_VERSION` as defects. A date or version token is adopted only when at least 50 percent of files carry it.
2. **Run** `python scripts/naming_audit.py <folder> --convention "<pattern>" --plan <outside-the-tree>/plan.csv`. Add `--date-order dmy|mdy` only after asking the user which order their numeric dates use; without it `03-04-2026` stays `AMBIGUOUS_DATE`. Add `--prefix-len <n>` with the character length of the folder the tree will sit in once synced. Add `--date-from-mtime` only if the user accepts the file's modified date as the name date (copying and syncing often resets it). Add `--ascii` if the drive must be ASCII-only.
3. **Read** the JSON in this order: `collisions` (two names that become one file on Windows and default macOS volumes; check `identical_content` before suggesting which to keep), `violations`, `version_series`, `needs_decision`, `held_back`.
4. **Plan.** `rename_plan` holds only names that come out fully conforming. Names that need a human choice are in `needs_decision` with a `partial` mechanical clean-up. A rename that would collide with another name, renamed or not, is moved to `held_back`. `plan_is_collision_free` must be `true`; it is re-verified on the end state of all files and folders. The CSV (`old,new`) lists each file's end-state path and so includes files that only move because a folder was renamed; `dir_renames` lists the folders.
5. **Report** in the fixed shape below. Tell the user to apply the plan on a copy or after a backup, because documents, project files and links that point to a file by path break when it is renamed.

## Defect codes

| Code | Meaning | Handling |
|---|---|---|
| `SPACE`, `MIXED_CASE`, `UPPER_EXT`, `DOUBLE_SEPARATOR`, `TRAILING_DOT_SPACE`, `UNICODE_FORM` | cosmetic and sync-hostile | auto fix |
| `NON_ASCII` (only with `--ascii`) | accents or other scripts | auto fix for accents (folded to plain letters); decision for other scripts |
| `FORBIDDEN_CHAR` | one of `< > : " \| ? *` or a control character | auto fix (replaced by a separator) |
| `RISKY_CHAR` | `# % & { } $ ! ' ` @ + = ; , ^ ~ [ ] ( )` break URLs, shells or globs | auto fix |
| `NON_SORTABLE_DATE`, `NON_ISO_DATE` | `03.04.2026`, `12 Mar 2026`, `2026.03.04` | auto fix when unambiguous |
| `AMBIGUOUS_DATE` | both numbers 12 or below, or a two-digit year | ask the user; never guess |
| `VERSION_FORMAT` | `v2`, `V2`, `rev2` against `v02` | auto fix (digits zero-padded to the width) |
| `DATE_POSITION` | one date present but not first | auto fix when exactly one date |
| `NO_DATE`, `NO_VERSION` | the convention requires the token | decision; never invent a version; a date only with `--date-from-mtime` |
| `FINAL_STYLE` | tokens like `final`, `final2`, `latest`, `newest`, `real`, `actual`, `usethis` | decision: the user says which version number it is |
| `COPY_SUFFIX` | `(1)`, `- Copy`, `copy 2`, `Copy of` | decision: which file is real |
| `DUPLICATE_VERSION` | two files in one series have the same number | decision, excluded from the plan |
| `RESERVED_NAME` | `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9` as a name | decision |
| `OVER_LENGTH` | path longer than `--max-path` (default 200) plus `--prefix-len` | decision: shorten a folder or the name |
| `LONG_NAME` | one name over 100 characters | decision |
| `PATTERN_MISMATCH` | no other code explains the mismatch | decision |

Read [references/rules.md](references/rules.md) only when a date, version, character or collision decision is in doubt: it holds the date conversion table, the series key, the character sets, the sources for the Windows and macOS facts, and the plan procedure. Folders are checked for the character, space, reserved, length and Unicode codes only. Names starting with a dot, `~$` lock files, `Thumbs.db` and `.DS_Store` are skipped unless `--include-hidden` is given (it covers only dot names); symbolic links are never followed.

## Version rule

The highest number is the latest version, not the newest timestamp. Series are grouped by folder, extension and the name before the version tag with any leading date removed. `version_series` reports `latest_by_number`, `latest_by_mtime`, `mtime_disagrees`, duplicate numbers and gaps. When the highest number is shared by two files, `latest_by_number` is `null` and `latest_ambiguous` is `true`: say so and ask. Do not call a file the latest because it was saved last.

## Output contract

One JSON document on stdout: `convention` (`source`, `pattern`, `needs_confirmation`, `evidence` when inferred), `files_total`, `dirs_total`, `files_without_violations`, `violations[]` (`path`, `kind`, `codes[]`, `fix` = `auto`, `needs_decision` or `held_back`), `violations_by_code`, `collisions[]` (`paths`, `kind`, `identical_content`), `version_series[]`, `rename_plan[]` (`old`, `new`, `reasons[]`), `dir_renames[]`, `held_back[]`, `needs_decision[]` (`path`, `remaining[]`, `partial`), `plan_is_collision_free`, `plan_problems`, `max_path`, `prefix_len`, `ignored`, `walk_errors`, `plan_written`. Exit 0 means nothing found, 1 means findings, 2 means a usage error with the reason on stderr. Run the script; do not edit it.

The script refuses to write `--plan` or `--report` onto the root, anything inside the root, the listing or any scanned file, even with `--force`.

## Report format

```
Convention: <pattern>, <given by the user | inferred and confirmed>
Scanned: <files> files, <dirs> folders, <n> ignored
Collisions: <list, or none>
Defects: <counts by code>
Plan: <n> renames in <path>, collision free: <yes/no>; held back: <n>; needs your decision: <n>
Decisions needed: <names with the question for each>
Not checked: file contents, links that point to these files, names beyond the listing, path limits of tools outside the drive
```

## Limits

- Dates are recognised only in the forms in the table; a number that merely looks like a date in a name can be rewritten, so read each date change.
- Thresholds (200 characters of path, 100 of name, 50 percent for inference) are house working values, not platform limits. Check the real limit of the drive being used.
- Collisions are found by case and Unicode form, not by similar spelling or by file content, except that files inside a collision group are hashed to say whether they are identical.
- It audits names, never what is inside the files.
- Without Python: list the names, lower-case them to find collisions by hand, and apply the table above one name at a time; say that the check was manual.
