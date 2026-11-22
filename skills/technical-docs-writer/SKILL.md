---
name: technical-docs-writer
description: Writes and audits README, API reference, how-to, tutorial and runbook pages. Use when the user asks to write or fix a README, API docs, how-to guide, runbook or tutorial, or says the docs are stale, mixed up or the examples no longer work. Splits pages by type with required sections, runs code samples before pasting them, adds a dated last-verified line, and audits a docs folder by script for missing sections, untagged code blocks, broken relative links, key-shaped secrets and stale dates. Do not use for docstrings, code comments, release notes, decision records, OpenAPI generation, or marketing copy.
license: Apache-2.0
compatibility: The audit script needs Python 3.9 or newer, standard library only, no network. Without Python, follow the section tables and the finding table by hand.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Technical docs writer

One page has one job. Write the page for that job, prove every command on it by running it, and stamp it with the date and version it was proved against.

## 1. Pick the type

| The reader wants to... | Type | Required sections (heading wording the audit accepts) | Last-verified line |
|---|---|---|---|
| decide whether to use it and start in minutes | readme | what it is (intro paragraph or Overview), Install, Usage, License | optional |
| look up an exact name, option, status code | reference | Endpoints or Parameters, Errors, Examples | required |
| get one real task done | how-to | Prerequisites, Steps (or 3+ numbered items), Verify | required |
| learn by building something small | tutorial | What you will build, Prerequisites, Steps, Summary or Next steps | required |
| understand why it is built this way | explanation | Background, How it works, Trade-offs | not needed |
| fix a live problem under stress | runbook | Symptoms or When to use, Procedure, Verification, Rollback, Escalation | required |

A page that needs two types is two pages; link them. A reference table inside a how-to stops it being skimmable; a "why" essay inside a runbook gets skipped by the on-call. Read [references/doc-types.md](references/doc-types.md) for the section skeleton of the type you are writing, and only that type's part.

## 2. Workflow

```
- [ ] 1 Baseline: audit the existing docs
- [ ] 2 Collect facts from the source, not from old docs
- [ ] 3 Draft from the skeleton
- [ ] 4 Run every command and sample
- [ ] 5 Add the last-verified line
- [ ] 6 Audit again, fix, repeat
- [ ] 7 Report
```

1. **Baseline.** If docs exist, run `python scripts/docs_audit.py <docs-folder>` first and keep the JSON; it shows what was already wrong before you touched anything.
2. **Collect facts** from the code, `--help` output, config files and tests. Old docs are a lead, never a source. A command, flag, default or status code you can find neither in the source nor in a run goes into the report as unknown, not onto the page.
3. **Draft** with the headings from the skeleton. Steps: 3 to 12, one action each, imperative verb first, each command in its own fenced block; a step that needs two commands is two steps. README: what it is in at most 3 sentences, first working command within the first 40 lines. Runbook step: command, expected output, and what to do if the output differs.
4. **Run every command and sample** before it enters the page:
   1. Use a clean directory and the exact version the page names. Pin versions in install lines (`pkg==1.2.3`).
   2. Run it. Paste the real output, exit code included when it matters. Shorten output only with a visible `...` line.
   3. If a command is destructive, or needs production access, credentials or money, do not run it against a real system. Run it in a scratch environment, or leave it unrun and put the line `Not run: <reason>` under the block. Every unrun block is listed in the report.
   4. A sample that fails is a finding. Fix the page only if the page was wrong; if the tool is broken, tell the user.
   5. Replace secrets with placeholders (`<YOUR_TOKEN>`); never paste a real key, even to make an example look real.
5. **Last-verified line**, directly under the title: `Last verified: 2026-11-21 against v2.3.1`. The date is the day you ran the commands (read it from the system, do not guess); the version is the release or commit you ran. Never change the date without re-running the commands, and never copy another page's line.
6. **Audit** the files you touched: `python scripts/docs_audit.py <folder> --today <today>`; fix by the table in section 3; re-run until `ok` is true. Do not edit the script to make a check pass.
7. **Report** in this shape:

```
Pages: <path - type - written or changed>
Run: <commands executed, in which environment and version>
Not run: <blocks left unrun and why>
Audit: <errors and warnings before and after>
Unknown: <facts the source did not settle>
Owner action: <revoke a leaked key, fill a contact, decide a policy>
```

## 3. Handling audit findings

| rule | severity | fix | trap |
|---|---|---|---|
| missing-section | error | add the section with real content, or write `Unknown: owner to fill` | an empty heading just to pass |
| broken-link | error | correct the path or its letter case; if the target page should exist but does not, tell the user | deleting a link the reader needs |
| broken-anchor | warning | use the heading's real slug (lowercase, spaces to hyphens) | renaming a heading other pages link to |
| code-no-language | warning | `bash`, `json`, `python`, `yaml`, or `text` for plain output | tagging output as `bash` so it looks like commands |
| secret-in-doc | error | remove it AND tell the owner to revoke it; history keeps the old value | removing without revoking |
| no-last-verified, stale-verified | warning | run the commands, then set date and version | bumping the date without running anything |
| bad-verified-date, future-verified-date | error | an ISO date no later than today | a future "review due" date in this line |
| unclosed-fence | error | close the fence where the code really ends | closing it at end of file and swallowing prose |
| no-h1 | warning | one `# Title` naming the task or the thing | several H1s |

Staleness limit: the default is 90 days. Use `--max-age-days 30` for runbooks that guard production and 180 for READMEs and explanations; run it per folder. A page is also stale when the tool's version moves on, whatever the date says.

## 4. Script

`scripts/docs_audit.py <folder-or-file> [--max-age-days N] [--today YYYY-MM-DD] [--require-version] [--strict]`: run it, do not read it. It reads `.md`, `.mdx` and `.markdown` files (skipping `.git`, `node_modules`, `vendor`, `dist`, `build`, `site`, venvs), writes nothing and prints one JSON object:

```
{"schema_version": 1, "command": "audit", "root": str, "today": "YYYY-MM-DD", "max_age_days": int,
 "files_scanned": int,
 "files": [{"path": str, "doc_type": readme|reference|how-to|tutorial|explanation|runbook|unknown,
            "detected_by": front-matter|path|headings|none,
            "findings": [{"rule": str, "severity": "error"|"warning", "line": int, "message": str}]}],
 "summary": {"findings": int, "errors": int, "warnings": int, "by_rule": {}, "by_type": {}},
 "ok": bool}
```

Type detection order: `doc_type:` or `type:` in front matter, then path (a README file name, or a folder or file name containing runbook, how-to, tutorial, reference or explanation), then heading scoring (at least 2 signals and a clear winner). `unknown` skips the section check, so set `doc_type:` in front matter when a page is misdetected. Exit 0 when there are no errors (and no warnings with `--strict`), 1 otherwise, 2 for an unreadable path or a bad option. Pass `--today` in tests and reports so results can be reproduced.

Without Python: check each page against the section table, look at every fence for a language tag, open each relative link, and read the verified line by hand; say in the report that the audit was manual.

## Limits

- The audit reads structure and text. It cannot tell whether a command is correct, a section is useful or a page is true; only running the commands does.
- Type detection is a heuristic, and paths are relative to the folder you audit: a runbook found by folder name when you audit the whole tree is found by headings when you audit only its folder. Heading wording outside the accepted list counts as missing even when the content is there; use the table's wording or set `doc_type:`.
- Links are checked for local files and in-repo anchors only. External URLs, links built by a site generator and custom heading ids are not checked.
- The secret check matches six common key shapes. It does not find passwords in prose or unusual tokens.
- Thresholds (90 days, 3 to 12 steps, 40 lines) are working values, not measured optima.
- Only Markdown is audited; reStructuredText, AsciiDoc and generated HTML are not.
