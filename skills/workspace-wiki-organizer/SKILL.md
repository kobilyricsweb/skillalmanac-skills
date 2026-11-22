---
name: workspace-wiki-organizer
description: Audits an exported team wiki (Notion, Confluence or similar, as Markdown or HTML files) for pages with no owner, stale pages, near-duplicate titles across spaces, orphan pages and broken internal links, then proposes an archive and merge plan, using a read-only script that prints strict JSON. Use when the user says clean up our wiki, wiki audit, find stale or outdated docs, who owns this page, duplicate pages across spaces, what can we archive, or the wiki is a mess. Do not use for a personal notes vault, writing or rewriting wiki content, live Notion or Confluence access, or website SEO.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. It reads an exported folder and uses no network. Without Python, follow the manual fallback in the Script section.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Workspace wiki organizer

Turn a team wiki export into an evidence-based cleanup plan: who owns what, what is stale, what exists twice, what nobody can reach, what is broken. The script measures; you interpret and propose; a person approves. Nothing in the export is ever changed.

Scope: a shared team or company wiki. A single person's Markdown notes belong to the personal-vault skill, not here.

## Workflow

```
- [ ] 1 Get an export folder (never audit a live space)
- [ ] 2 Choose the reference date and thresholds
- [ ] 3 Run the audit script
- [ ] 4 Check the notes field and the traps below
- [ ] 5 Turn findings into a plan the owners can act on
- [ ] 6 Report in the fixed format
```

1. **Export.** Ask the user for a folder with the Markdown or HTML export. If they only have a live space, tell them how to export it: read [references/export_formats.md](references/export_formats.md) (what each export looks like, where owner and date information survives, and which of them lose it). Do not ask for credentials.
2. **Thresholds.** Default staleness is 180 days. Pick per page type from the table below when the user names the kind of wiki; state the choice. Always pass `--today` with the real date so the run is repeatable.
3. **Run** (from the skill folder or with an absolute path; the folder path is yours to pass):

```bash
python scripts/wiki_audit.py <export-folder> --today YYYY-MM-DD --stale-days 180
```

   Add `--mtime-fallback ignore` when file times are export times (see traps). Add `--include-pages` for a per-page table. Run the script; do not edit it to make a result look better.
4. **Read the `notes` array first.** `mtime_unreliable` means the staleness numbers for undated pages are wrong; say so and re-run with `ignore`.
5. **Plan.** Start from the script's `plan`, then apply the rules in "Turning findings into actions". Group by owner or space so each owner receives one list.
6. **Report** in the format below. Never claim the cleanup happened.

## Staleness thresholds by page type

| Page type | Stale after | Why |
|---|---|---|
| Runbooks, on-call, incident procedures | 90 days | Wrong steps cause outages; systems change quarterly |
| Onboarding, how-to, process pages | 180 days (default) | Tools and teams change about twice a year |
| Policies, security, compliance | 365 days | Reviewed on an annual cycle |
| Architecture decision records, post-mortems | never stale | They are history; judge them by links, not age |
| Meeting notes, retros, weekly updates | do not use staleness | Dated by nature; archive by folder once past 90 days |

A page is stale only on its own last-update date. A stale page that many pages link to is more urgent to review, not less.

## Script

`scripts/wiki_audit.py <folder> [options]`: run it; read-only; prints one strict JSON document (no NaN); exit 0 when the audit finished, 2 on a bad folder or argument, 1 only with `--fail-on-findings` and findings present.

| Option | Default | Meaning |
|---|---|---|
| `--stale-days N` | 180 | Age at which a page is listed as stale |
| `--today YYYY-MM-DD` | today | Reference date |
| `--mtime-fallback use/ignore` | use | Date undated pages by file modified time, or list them as `undated` |
| `--dup-threshold X` | 0.88 | Title similarity (0.5 to 1.0) for duplicate candidates |
| `--max-depth N`, `--wide-folder N` | 4, 50 | Folders deep and pages per folder before a flag |
| `--limit N` | 500 | Items per list; `truncated` shows the real totals |

Top-level JSON keys (all present on every run): `tool`, `schema_version` (1), `read_only` (true), `root`, `today`, `params`, `summary` (counts, plus `plan_actions` per action), `ownerless` (`path`, `reason` = missing or placeholder), `stale` (`path`, `updated`, `date_source` = metadata, meta, body or mtime, `age_days`), `undated`, `orphans`, `entry_points`, `broken_links` (`source`, `line`, `target`, `reason` = missing_target, case_mismatch, outside_export or absolute_local_path), `duplicate_titles` (`a`, `b`, `title_similarity`, `body_similarity`, `relation`, `cross_space`), `identical_content` (groups of paths), `deep_pages`, `wide_folders`, `plan`, `skipped`, `notes`, `truncated`; with `--include-pages` also `pages`.

How it decides: an owner is a value on an `owner`, `maintainer`, `dri` or `steward` line or field, and the values TBD, none, unknown, unassigned, a template placeholder or an empty value count as no owner; "Created by" never counts. The update date is the newest of the metadata and "Last updated/edited/modified/reviewed" dates, ignoring future dates. Duplicate titles are compared across different folders only, after dropping copy, old, draft and version words; titles that differ in any number (sprint 12 and 13, Q1 and Q2) are never paired, and generic titles such as Overview or FAQ are skipped. Orphans are pages no other page links to, excluding index, README, home, summary and sidebar pages.

**Manual fallback** (no Python): list owner lines with a text search for `owner:` across the export, sort files by modified date, and for each page title search the folder for the same words. The result will be slower and will miss broken links; say so in the report.

## Traps that change the answer

- **Export time stamps.** After an unzip or a sync, every file may carry the same modified time. When the script reports `mtime_unreliable`, do not call those pages fresh; call them undated and ask the owner of the space for a date source.
- **Navigation that is not in the export.** A sidebar or space home that exports as a separate file still counts, but a tree menu built by the tool does not. A large orphan count right after an export is a reason to ask where navigation lives before archiving anything.
- **`case_mismatch`** links work on Windows and macOS and break on Linux web servers; treat them as broken.
- **`title_clash_only`** (same title, different content) is a naming problem, not a duplicate; never merge those.
- **Departed owners.** The script cannot know who left. Ask for a current roster, then treat pages owned by people not on it as ownerless.
- **Anchors and external links** are not checked. A link can resolve and still point at a heading that was renamed.

## Turning findings into actions

| Evidence | Action | Notes |
|---|---|---|
| Identical or near-identical content in two places | `merge` into the newer, better-linked page | Redirect or relink inbound links to the keeper |
| Stale, nothing links to it, no owner | `archive`, high confidence | Still give a notice period |
| Stale, nothing links to it, has owner | `archive`, medium | Owner confirms first |
| No owner (alone, or also stale but linked) | `assign_owner` | A person or a team with a contact channel |
| Stale but linked, has owner | `review_with_owner` | Owner updates, archives or links to a replacement |
| Fresh orphan with owner | `review_with_owner`, low | Link it from a parent page or archive it |
| Broken internal links | `fix_links` | Page owner repairs or removes the link |
| Same title, different content | `disambiguate` | Rename so titles differ |

Plan confidence drops one level when a page's date came from file modified time. Default archive procedure to propose (the user's policy wins): notify the owner and wait 14 days; move the page to an Archive area keeping its original path; put a banner with the archive date, reason and replacement link at the top; keep it 12 months before anyone considers deleting; never delete in the first pass. Details and variants: [references/archive_policy.md](references/archive_policy.md), read when the user asks how to run the archive step or what policy to adopt.

## Report format

```
Audited: <folder>, <n> pages, reference date <date>, stale after <n> days
Ownership: <n> pages without an owner (<placeholder count> placeholders)
Stale: <n> pages (<n> dated from file time)
Duplicates: <n> merge candidates, <n> title clashes
Reachability: <n> orphans, <n> broken links
Plan: <counts per action>, then the actions grouped by owner or space
Not checked: <anchors, external links, attachments' content, live space, departed owners>
```

List the plan entries with path, action, confidence and one reason. Offer to draft the owner notices; do not send them.

## Limits

- Reads exports only; it cannot see comments, permissions, page views or edit history, so "stale" means "not updated", not "unused".
- Titles and links are compared as text. Two pages about the same topic with different words are not found.
- Date and owner detection recognise common patterns (front matter, a labelled line, a properties table, meta tags); an export that stores them elsewhere shows everything as ownerless or undated.
- Thresholds (180 days, 0.88 title similarity, 0.80 and 0.30 body overlap, depth 4, 50 pages) are working values, not measured optima.
- Files over 2 MB are skipped and listed under `skipped`.
- The plan is a proposal. This skill never edits, moves or deletes pages.
