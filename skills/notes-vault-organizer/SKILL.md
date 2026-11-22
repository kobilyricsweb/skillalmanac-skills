---
name: notes-vault-organizer
description: Tidies a Markdown notes vault (Obsidian-style wikilinks, frontmatter, tags) without losing anything. Use when the user says clean up my vault, organize my notes, fix broken links, merge duplicate tags, find orphan notes or tidy my Obsidian folder. A read-only script finds broken and ambiguous links, orphans, duplicate titles and content, tag variants and notes without frontmatter, then proposes a strict-JSON move plan that is validated, approved and logged before any file moves. Do not use for writing or summarising notes, notes kept in an app database instead of Markdown files, code repository cleanup, or deleting files.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual fallback below.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
  license: Apache-2.0
---

# Notes vault organizer

A vault is someone's memory. The job is to make it easier to navigate and to lose nothing: every change is proposed first, approved by the owner, reversible, and written down.

## Safety rules

1. **Never delete.** No file is removed, emptied, overwritten or merged away. "Remove" always means "move to `_review/` for the owner to decide". If asked to delete, move instead and say the owner can empty `_review/` themselves.
2. **Scan before you touch.** The first contact with the vault is `scripts/vault_scan.py`, which cannot write. Do not edit the vault until the owner approves specific plan ids.
3. **Moves, not copies.** One operation per file: a move (`git mv` inside a git repo, otherwise the OS move). Never copy then delete.
4. **Back up first.** Require a clean git working tree with a commit, or a copy of the vault the owner confirms exists. Stop and ask if there is neither. Do not run while a sync client is mid-upload or while the vault is open for editing in another tool.
5. **Log every change** (step 6). A change without a log line is a defect.
6. **Content edits are separate from moves.** Fixing a link text, renaming a tag or adding frontmatter edits a note's text. Each kind needs its own approval and a before/after line in the log.

## Workflow

```
- [ ] 1 Scope and backup confirmed
- [ ] 2 Scan, save JSON outside the vault
- [ ] 3 Report findings, decide nothing yet
- [ ] 4 Draft proposals, validate the move plan
- [ ] 5 Owner approves by id
- [ ] 6 Apply approved items only, log each
- [ ] 7 Re-scan and compare
- [ ] 8 Report
```

1. **Scope.** Get the vault folder. Ask which folders to leave alone (templates, daily notes, attachments, an exported archive); pass them as `--exclude "Templates/*"`. Confirm the backup (safety rule 4).
2. **Scan.** Run it and save the output outside the vault, for example next to the change log:

```bash
python scripts/vault_scan.py scan <vault> --exclude "Templates/*" > scan_before.json
```

   Dot-folders (`.obsidian`, `.git`, `.trash`) are skipped automatically. Read the `counts` block first. Keep `tree_sha256`: a second scan of an untouched vault must give the same value.
3. **Report findings** using the shape in step 8, section "Found". Say what is normal: orphans are often fine (index notes, daily notes, scratch), and one broken link may be a deliberate placeholder for a note not yet written.
4. **Draft proposals** per category using the table below. Moves come from `move_plan.moves`; edit the plan (drop items, change a destination) rather than invent moves by hand, then check it:

```bash
python scripts/vault_scan.py validate-plan <vault> plan.json
```

   It must print `"ok": true`. It rejects missing sources, taken destinations, paths that leave the vault, double moves and any action other than a move. Do not edit the script to make a plan pass.
5. **Approval.** Show a table of ids with from, to and reason, and wait. Approval by id (`m1, m3`) covers only those ids. "Do whatever you think" is not approval for edits to note text.
6. **Apply** approved ids only, one at a time. After each move check the destination exists and the source does not. Append a log entry (format in [assets/changelog-template.md](assets/changelog-template.md)) with the id, from, to, time and the undo move. Keep the log outside the vault unless the owner asks for it inside.
7. **Re-scan** to `scan_after.json` and compare: `notes` unchanged; `broken_links` not higher than before except by links the plan declared in `path_links_affected`; no new `unreadable`. If a count got worse, undo the last batch from the log and report it.
8. **Report** in this fixed shape:

```
Found: <counts: broken links, ambiguous links, orphans, duplicate titles/content, tag groups, notes without frontmatter>
Proposed: <ids with from, to, confidence>
Applied: <ids done, with log path> or "nothing applied"
Compare: <before and after counts; tree hash before and after>
Left for the owner: <everything not approved, ambiguous, or needing their judgement>
Not checked: <e.g. heading and block links, links from outside the vault, other tools reading these paths>
```

## What to do with each finding

| Finding | Meaning | Proposal |
|---|---|---|
| `broken_links` | No note or file matches the target | If `suggestions` has one close name, propose that link-text fix as an edit. Otherwise list it; never create a note to hide it |
| `ambiguous_links` | A name matches several notes; the editor picks one by its own rule | Propose renaming one note or writing the link with its folder path. Needs the owner's pick |
| `orphans` | No other note links here | Only `stub-orphan` moves are proposed. Everything else is informational; ask before suggesting links |
| `duplicate_titles` with `same_filename` | Two files share a name, so name-only links are ambiguous | Owner decides which to rename |
| `duplicate_content` | Byte-for-byte same text after trimming | Move the extra copy to `_review/duplicates/`. The kept copy has more inbound links |
| `tag_variants` | Same tag spelled differently | Propose a rename table (variant to `suggested`) for approval. Replace whole tags only, in frontmatter and in body text, never inside words or code |
| `missing_frontmatter` | No `---` block, or an empty or unclosed one | Propose a minimal block (`title` from the first heading). Never invent tags or dates. Unclosed blocks need a manual look |
| `move_plan` | Rules: duplicate-content (high), stub-orphan (medium), tag-folder (medium) | Show with reasons. Check `path_links_affected`: links written with a folder path or as ordinary Markdown links break when the file moves and must be fixed in the same approved batch |

The `tag-folder` rule moves only root-level notes whose `type` or tag matches an existing top-level folder name (case and plural insensitive). It never creates folders other than `_review/`.

## The scan output contract

`scan` prints one JSON object, `schema_version` "1", UTF-8, no comments or NaN. Top-level keys: `read_only` (always true), `vault`, `tree_sha256`, `counts`, `broken_links`, `ambiguous_links`, `orphans`, `duplicate_titles`, `duplicate_content`, `tag_variants`, `missing_frontmatter`, `unreadable`, `move_plan`, `truncated`. All paths are relative to the vault with forward slashes. Lists hold at most `--max-items` entries (default 200); `counts` are always the true totals and `truncated` says how many were left out.

`move_plan` is `{"dry_run": true, "applied": false, "moves": [...], "skipped": [...]}`. Each move is `{"id", "from", "to", "rule", "confidence", "reason", "path_links_affected"}`. Skipped items say why (destination exists, tags point to several folders). Field details and every other record shape: [references/json-schema.md](references/json-schema.md).

## Scripts

- `scripts/vault_scan.py scan <vault> [--exclude GLOB] [--max-items N]`: run it. Read-only. Exit 0 when the scan finished, 2 on a missing folder or no notes.
- `scripts/vault_scan.py validate-plan <vault> <plan.json>`: run it. Exit 0 valid, 1 with a `problems` list, 2 unreadable plan.

Do not modify either script. Read [references/vault-link-rules.md](references/vault-link-rules.md) only when a finding looks wrong (links the script resolved or missed, a move that might break a path link, a tag the script grouped oddly).

## Manual fallback without Python

Search the vault for `[[` and list each distinct target; check each name against the file list, case-insensitively. List files whose first line is not `---`. Collect `#tag` words and the `tags:` lists and compare spellings by eye. Propose moves in the same table, validate by hand (source exists, destination free, inside the vault), and follow safety rules 1 to 6 unchanged. Say in the report that the findings are from manual search.

## Limits

- Links are matched by note name, alias, folder path and ordinary Markdown links. Heading and block parts of a link (`#Heading`, `#^id`) are not checked; a link to a missing heading counts as fine.
- Links from outside the vault (a website build, another app, bookmarks) are invisible, so a move may break them.
- Frontmatter is read with a small parser: top-level scalars, `[a, b]` lists and block lists. Nested properties are ignored.
- Tag grouping uses crude English singular rules. It can miss pairs such as movie and movies and can group unrelated words that share a stem; the owner confirms every rename.
- The `tag-folder` and `stub-orphan` rules are heuristics; the 15-word stub limit is a working value.
- Notes over 2 MB are reported as unreadable and skipped. Files with other extensions are only checked as link targets.
- A scan is a snapshot. Anything edited during a run can make the result stale; re-scan before applying.
