# Workspace wiki organizer

## One-line summary

Audits an exported team wiki for missing owners, stale pages, duplicates, orphans and broken links, and proposes an archive plan.

## What it does

The skill takes a folder holding a Notion, Confluence or Git-wiki export (Markdown or HTML) and runs a read-only Python script over it. The script reads owner lines, last-updated dates, titles, bodies and internal links, then prints one strict JSON report: pages without an owner, pages older than a threshold, same-titled pages in different folders with a body-similarity verdict, pages no other page links to, links that do not resolve, and over-deep or over-wide folders. The agent turns that report into a proposed plan (merge, archive, assign owner, review with owner, fix links, disambiguate) with a confidence per entry, using staleness thresholds per page type and a default archive procedure.

## Capabilities

- Owner detection from front matter, labelled lines, HTML properties tables and meta tags; placeholders such as TBD count as no owner
- Staleness from the dates written in the page, with file modified time as an opt-out fallback and a warning when export time stamps make it unreliable
- Duplicate detection across folders that skips generic titles and numbered siblings (Sprint 12 versus Sprint 13) and separates "same content" from "same title, different content"
- Broken-link check including percent-encoded Notion paths, wiki-style links and case-only mismatches
- Strict JSON output with a documented contract, exit codes, and a proof (in the fixture runner) that no file is modified

## How it differs from notes-vault-organizer

`notes-vault-organizer` is for one person's Markdown vault: tags, daily notes, personal linking. This skill is for a shared team wiki and answers different questions: who is accountable for each page, which pages other people still rely on, which copies exist in other spaces, and what a team can safely archive. It reads Notion/Confluence-style exports including HTML, and its plan is built around owners and notice periods, not personal note hygiene.

## When to use

- "Our wiki is a mess, what can we archive?"
- "Which pages have no owner?" / "what hasn't been updated in six months?"
- "We have the same guide in three spaces."
- Preparing a quarterly wiki cleanup from an export

## When not to use

- A personal notes vault (use the personal vault skill)
- Writing, rewriting or translating wiki pages
- Working against a live Notion or Confluence space through an API
- Website SEO or crawl audits

## Requirements

Python 3.9 or newer, standard library only. No network. Tested on Windows 11 with Python 3.11; other systems untested.

## Install

Copy the `workspace-wiki-organizer` folder into the tool's skills folder (for example `.claude/skills/` or `.agents/skills/`). Pinned install commands are produced at publication.

## Examples

Prompt: "Audit our wiki export in `wiki_bad`. Today is 2026-11-21, stale after 180 days. Give me an archive and merge plan."

Real output of `python scripts/wiki_audit.py evals/fixtures/wiki_bad --today 2026-11-21 --mtime-fallback ignore` (summary and first plan entries, from the fixture run):

```
pages 16, ownerless 3, stale 5, undated 1, orphans 4, broken_links 5,
duplicate_title_pairs 3, identical_content_groups 1, deep_pages 1
plan_actions: merge 1, archive 3, assign_owner 1, fix_links 2, disambiguate 2

merge     growth/pricing-model.md -> product/pricing.md   (high)
archive   engineering/old-vpn-setup.md                    (medium: owner Priya N must confirm)
archive   engineering/ownerless-orphan.md                 (high)
archive   legacy.html                                     (high)
assign_owner engineering/runbook-db.md                    (high: "Owner: TBD", also stale, still linked)
```

Second prompt: "Is `wiki_good` healthy?" Output: 3 pages, zero findings in every category, empty plan.

## Limits

Reads exports only; "stale" means not updated, not unused. Titles and links are compared as text. Date and owner detection cover common patterns only. Thresholds are working values. Files over 2 MB are skipped. The plan is a proposal; nothing is edited, moved or deleted.

## Evidence

Static lint and script fixtures only; see VERIFICATION.md. Efficacy, trigger and cross-tool tests have not been run.

## Demo script (60 to 90 seconds)

1. Prompt: "Here's our wiki export, what can we archive?" with the `wiki_bad` folder.
2. The agent runs the audit and shows the summary: 16 pages, 3 without owner, 5 stale, 4 orphans, 5 broken links.
3. It points out the traps: the two "Pricing Model" pages with different content are renamed, not merged; the runbook is stale but still linked, so it gets an owner first.
4. Result: 9 plan entries grouped by action, with confidence and a 14-day notice before anything moves.

## FAQ seeds

- Does it need network or an account? No; it reads a local export.
- Does it change my wiki? No; the script never writes, and the fixture runner proves it.
- Does it work with live Notion or Confluence? No, export first.
- Why are my pages all "fresh"? File times may be export times; the script warns about that.
- How is it different from the personal vault skill? See above.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft; static lint and fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has taken place yet.
