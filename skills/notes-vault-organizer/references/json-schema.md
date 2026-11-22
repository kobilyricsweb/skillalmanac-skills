## Contents

- Scan output, top level
- Record shapes
- move_plan
- validate-plan output
- Stability rules

# JSON shapes

Everything is UTF-8 JSON, indented, with no NaN or comments. Paths are relative to the vault root with forward slashes and keep their original case. Lists are sorted in scan order (root files first, then folders alphabetically), except where noted.

## Scan output, top level

| Key | Type | Meaning |
|---|---|---|
| `schema_version` | string | `"1"`. Changes only when a field is removed or renamed |
| `command` | string | `"scan"` |
| `read_only` | boolean | Always `true` |
| `vault` | string | Absolute path as scanned, forward slashes |
| `tree_sha256` | string | Hash over every note's bytes plus every attachment's name and size. Same value on two scans means nothing changed |
| `counts` | object | True totals: `notes`, `attachments`, `broken_links`, `ambiguous_links`, `orphans`, `duplicate_title_groups`, `duplicate_content_groups`, `tag_variant_groups`, `missing_frontmatter`, `planned_moves`, `skipped_moves`, `unreadable` |
| `broken_links` ... `unreadable` | arrays | Records below, capped at `--max-items` each |
| `move_plan` | object | See below; never capped |
| `truncated` | object | Maps a list name to the number of records left out; empty when nothing was capped |

## Record shapes

`broken_links[]`: `source`, `line` (1-based, in the file), `kind` (`wikilink`, `embed` or `markdown`), `target` as written without alias or heading part, `suggestions` (up to three existing note paths whose name is a close match; empty for path-style and markdown links).

`ambiguous_links[]`: `source`, `line`, `target`, `candidates` (every note the name could mean, sorted). Each candidate counts as linked, so none of them is reported as an orphan because of this link.

`orphans[]`: `path`, `outbound_links` (count of link occurrences in the note, any kind, resolved or not), `tags`, `words` (body words after frontmatter), `has_frontmatter`.

`duplicate_titles[]`: `title` (case-folded, whitespace collapsed; the frontmatter `title` when present, otherwise the file name without `.md`), `paths`, `same_filename` (true when two of the files share a name, which makes name-only links ambiguous).

`duplicate_content[]`: `sha256` (first 16 hex characters of the hash of the trimmed text), `paths`. Empty notes are never grouped.

`tag_variants[]`: `key` (normalised spelling shared by the group), `suggested` (most used spelling; ties go to the lower-case one, then the shorter, then alphabetical), `variants[]` with `tag`, `notes` (number of notes using it) and `difference` (`suggested`, `case`, `separator` or `plural`). Tags come from frontmatter `tags`/`tag` and from `#tag` words in the body outside code.

`missing_frontmatter[]`: `path`, `reason` (`none`, `empty` or `unclosed`).

`unreadable[]`: `path`, `reason`.

## move_plan

```json
{
  "dry_run": true,
  "applied": false,
  "moves": [
    {"id": "m1", "from": "Scratch copy.md", "to": "_review/duplicates/Scratch copy.md",
     "rule": "duplicate-content", "confidence": "high",
     "reason": "identical content to Scratch.md (kept: more inbound links, then shorter path)",
     "path_links_affected": 0}
  ],
  "skipped": [
    {"from": "Gamma.md", "rule": "tag-folder", "reason": "destination exists: Projects/Gamma.md"}
  ]
}
```

Rules, in the order they claim a note: `duplicate-content` (high; destination `_review/duplicates/`), `stub-orphan` (medium; fewer than 15 words, no tags, no links in either direction; destination `_review/stubs/`), `tag-folder` (medium; root-level note whose `type` or tag matches exactly one existing top-level folder; destination that folder). A note is in at most one move. The file name never changes. `path_links_affected` counts the notes that link to the moved note with a folder path or an ordinary Markdown link, which stop working after the move.

## validate-plan output

```json
{"schema_version": "1", "command": "validate-plan", "ok": false, "moves_checked": 9,
 "problems": [{"code": "destination-exists", "index": 0, "detail": "already in the vault: Ideas.md"}]}
```

Input: a scan output, or any object with a `moves` list. Problem codes: `not-an-object`, `forbidden-action` (any `action` other than `move`), `unsafe-source`, `unsafe-destination` (empty, backslash, absolute, `..`, hidden folder), `source-missing`, `not-a-note` (only `.md` files may move), `noop`, `destination-exists` (case-insensitive), `duplicate-source`, `duplicate-destination`. `index` is the position in the `moves` list, starting at 0.

## Stability rules

A consumer must ignore keys it does not know. `ok`, `problems[].code` and the names above are stable within schema version 1.
