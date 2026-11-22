---
name: internal-link-orphan-finder
description: Finds orphan pages, unreachable pages, deep pages and broken internal links in a folder of HTML or Markdown files by building the internal link graph from relative links. Use when a site owner or SEO reviewer wants to know which pages have no inbound internal link, which pages sit more than 3 clicks from the index, or which internal links point to missing files, before a crawl or sitemap review. Do not use for external link checking, live URL crawling, sitemap generation, or rewriting content.
license: Apache-2.0
compatibility: Python 3.9+ standard library only, no network access (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Internal link orphan finder

This skill runs `scripts/link_graph.py` on one site folder, reads the JSON it prints,
and reports the findings in the fixed layout below. The script does the graph work;
your job is to run it once, check the result, and report it without changing the
site.

## Files in this skill

- `scripts/link_graph.py` - the scanner (stdlib only, read-only on inputs).
- `fixtures/smoke-site/` - a 5-page sample folder with one orphan and one broken link.
- `LICENSE.txt` - Apache-2.0 license text.

## Workflow

1. **Confirm the folder.** Required output: the absolute path of the site folder and
   the name of the root page. The folder must contain `index.html` or `index.md` at its
   top level. If not, stop (see Refuse / stop when).
2. **Run the scanner once.** Command:
   `python -I scripts/link_graph.py <site_dir>`
   Add `--out <report.json>` only if the user asked for a saved file. Required output:
   the exit code and the full JSON on stdout.
3. **Read the exit code.** 0 means no findings, 1 means findings exist, 2 means the
   input was refused. On 2, copy the one-line JSON error from stderr and stop.
4. **Check the counts.** Required output: the `summary` block. Confirm that
   `pages` equals the number of .html, .htm and .md files you expect. A mismatch
   usually means hidden folders or symbolic links were skipped; say so.
5. **Classify each finding** using the decision table below. Required output: one
   row per finding, with its class and the suggested fix category.
6. **Write the report** in the output contract below. Do not edit any file in the
   site folder. Do not add links on the user's behalf.

## Decision table

| Finding class | Source key | Rule | Suggested fix category |
|---|---|---|---|
| Orphan | `orphans` | No inbound internal link from any other page. Index is never an orphan. | Add at least one link from a page that is itself reachable from the index. |
| Unreachable | `unreachable` | Has an inbound link, but no click path from the index. | Link the cluster from a reachable page. |
| Deep | `deep_pages` | Click depth from the index is greater than 3. Working value, not an industry standard. | Add a link from a page at depth 1 or 2. |
| Broken | `broken_links` reason `missing_target` | Target does not resolve to a page or to any file in the folder. | Fix the path or remove the link. |
| Escape | `broken_links` reason `outside_site` | Relative path climbs above the site root. | Fix the path. |

Hub threshold: `top_hubs` lists the 5 pages with the most inbound links (working value).
A page is never reported as a hub with 0 inbound links.

Resolution order for an internal href (fixed, do not improvise): exact path, then
`.html`, then `.md`, then `index.html` or `index.md` inside the folder. Fragments
(`#...`) and query strings (`?...`) are stripped first. Schemes such as `mailto:` and
protocol-relative links are skipped and not counted.

## Output contract

Reply with these headings, in this order, and no others:

1. `## Summary` - one line: `pages=<n> findings=<n> exit=<0|1|2>`.
2. `## Findings` - a table with columns `class | page or source | target or depth | fix category`.
   One row per finding. Sort by class in the order of the decision table, then by page path.
3. `## Counts` - a table with columns `key | value` listing every key in `summary`.
4. `## Not checked` - a bulleted list. Always include: external links, rendered pages
   produced by templates, and any file the scanner skipped (hidden or symbolic).

If the exit code is 0, the Findings table has one row: `none | - | - | -`.

## Refuse / stop when

- The folder does not exist or is not a directory.
- The folder has no `index.html` or `index.md` at the top level.
- The folder holds more than 2000 pages, more than 5000 files, more than 8 levels of
  nesting, a single file over 2 MB, or more than 64 MB in total.
- The user asks you to write the report inside the scanned folder. The scanner refuses
  this too, so stop and ask for another location.
- The user asks you to fix links, delete pages, or change the site. This skill reports only.
- The user asks for external link status or live HTTP checks. This skill has no network access.

## Script contract (type A)

- Command line: `python -I scripts/link_graph.py <site_dir> [--out <report.json>]`
- Arguments: exactly one `<site_dir>`; optional `--out` path. Any other option exits 2.
- Input: `.html`, `.htm` and `.md` files, UTF-8 only. Hidden folders and symbolic links are skipped.
- Output keys on success: `tool`, `version`, `index`, `summary` (keys `files`, `pages`,
  `internal_links`, `orphans`, `unreachable`, `deep_pages`, `broken_links`, `findings`),
  `orphans`, `unreachable`, `deep_pages` (objects with `page`, `clicks`), `broken_links`
  (objects with `source`, `href`, `reason`), `top_hubs` (objects with `page`, `inbound`).
- Exit codes: 0 no findings; 1 at least one finding; 2 usage or input error. Error
  text is one line of JSON on stderr, for example `{"error": "no index.html or index.md at the site root"}`.
- `--out` is refused with exit 2 if it resolves to an input file, to a directory, or to
  a path inside the scanned folder.

## Limits

- Only relative links in href attributes and in Markdown link syntax (bracketed text
  followed by a parenthesised target) are read.
- Links built by scripts or templates are invisible to the scanner.
- A 3-click depth threshold is a working value chosen for this tool.
