---
name: notes-vault-organizer
description: Tidies a Markdown notes vault (wikilinks, frontmatter, tags) without losing anything. Use when the user says clean up my vault, organize my notes, fix broken links, merge duplicate tags, find orphan notes or tidy my Obsidian folder. A read-only script finds broken and ambiguous links, orphans, duplicate titles and content, tag variants and notes without frontmatter, reports exact findings in the format you ask for, applies precise briefs directly, and for vague requests proposes a validated plan and waits for approval. Do not use for writing or summarising notes, notes kept in an app database instead of Markdown files, code repository cleanup, or deleting files.
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

Lose nothing. Match the effort to the request, then answer in the format the user named.

## Step 1: classify the request (decide before scanning)

| Request | Mode | What to do |
|---|---|---|
| Read-only: audit, list, find, report | **AUDIT** | Scan, change nothing, answer in the requested shape |
| Precise brief naming the notes, tags or links and the change ("merge tag X into Y", "move notes with status: done to Archive/", "fix these links") | **DO IT** | The request is the approval. Apply exactly that, nothing extra |
| Vague or broad ("sort it out", "clean up", "tidy") | **PROPOSE** | Change nothing. Findings plus numbered proposals, wait for ids |
| One note, a handful of files, or a question | **PLAIN** | Skip the scan. Read the files, answer or edit directly |

If the vault is not Markdown files (app database, code repo), say so and stop. Never delete: "remove" means move to `_review/` and say the owner can empty it. Do not move or rewrite anything the brief did not name (no bonus tidying, no unasked folders).

## Step 2: scan (AUDIT, PROPOSE, and DO IT when more than about 10 notes)

```bash
python scripts/vault_scan.py scan <vault> [--exclude "Templates/*"] > ../scan_before.json
python scripts/vault_report.py ../scan_before.json [--sections broken,orphans,duplicates,tags,frontmatter,moves]
```

Save JSON outside the vault. `vault_report.py` prints one bullet per finding with paths and line numbers; copy from it, do not retype counts by hand. Dot-folders are skipped automatically. Orphans are often fine (index, daily, scratch notes); a broken link may be a deliberate placeholder.

## Step 3: apply (DO IT, or PROPOSE after the owner approves ids)

1. Backup: a clean git commit, or a copy the owner confirms. If the brief is precise and the folder is not under git, copy the affected files to `<vault>_backup` yourself and say so; do not stop to ask.
2. Moves: OS move or `git mv`, never copy-then-delete. Build `{"moves":[{"from","to"}]}` and run `python scripts/vault_scan.py validate-plan <vault> plan.json` (must print `"ok": true`). Do not edit the scripts to pass.
3. A moved note breaks links written with a folder path or ordinary Markdown links to a .md path; name-only `[[wikilinks]]` survive. Fix those links in the same batch, whole-target replacements only.
4. Tag renames: whole tags only, in frontmatter and body, never inside words, code spans or fences. Keep each file's line endings (LF or CRLF) and every other frontmatter line byte-for-byte. Never invent tags, dates or titles.
5. Verify each change (destination exists and source gone; or re-read the edited line). If a move fails midway, stop, list what was done, undo only that item.
6. Re-scan to `scan_after.json`: `notes` unchanged; `broken_links` not higher except links the plan declared; no new `unreadable`. If worse, undo the last batch and say so.

PROPOSE mode: show ids with from, to, reason; wait for "m1, m3". Approval covers only those ids; "do whatever you think" does not cover edits to note text.

| Finding | Proposal |
|---|---|
| `broken_links` with one close `suggestions` entry | link-text fix as an edit; otherwise list it, never create a note to hide it |
| `ambiguous_links`, same-filename duplicates | owner picks which note to rename or which path to write |
| `duplicate_content` | move the copy with fewer inbound links to `_review/duplicates/` |
| `tag_variants` | rename table variant -> `suggested` |
| `missing_frontmatter` | minimal block, `title` from first heading; unclosed blocks need a manual look |
| `orphans` | only `stub-orphan` (under 15 words, no tags, no links) moves; the rest informational |

## Step 4: answer

The user's stated format wins: exact headings, file name, word limit, bullet style. If they name an output file (report.md), write it, check it exists, and put the same content in the reply too; if it cannot be written, say so in one line. Never claim a file was written without checking.

Always give, in whatever shape fits: every note found or moved as its own bullet (path, or from -> to), what was left alone and why, what was not checked. Default shape when nothing was requested:

```
Found: <counts>
Changed: <each move/edit: from -> to, or "nothing changed">
Left for you: <ambiguous items and decisions>
Not checked: heading/block links, links from outside the vault
```

An AUDIT asking for two sections gets exactly those two headings with bullets, no extras. In AUDIT and PROPOSE the vault stays byte-identical (`tree_sha256` equal on a second scan).

## Limits

Heading and block link parts are not checked; links from outside the vault are invisible; frontmatter parser reads top-level scalars and lists only; tag grouping uses crude English plurals, so the owner confirms renames; notes over 2 MB are skipped. JSON shapes: [references/json-schema.md](references/json-schema.md). Link-resolution oddities: [references/vault-link-rules.md](references/vault-link-rules.md). Change log format if wanted: [assets/changelog-template.md](assets/changelog-template.md). Without Python: grep `[[` targets and compare with the file list by hand, and say the findings are from manual search.
