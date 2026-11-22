---
name: sitemap-index-builder
description: Builds a sitemap index XML file that references sitemap shard files, starting from a list of shard URLs. Use when a site has split its sitemaps into several shard files and needs one sitemap index file, or when shard URLs must be checked for https, the expected host, duplicate entries, lastmod format, and the 50,000 entry and 50,000 URL limits. Do not use for writing the shard files themselves, for crawling or fetching shard URLs, for submitting the index to a search engine, or for a site that has only one urlset file.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Sitemap index builder

This skill runs `scripts/sitemap_index.py` on a shard list and reports what it wrote and what it rejected. The script does not fetch any URL. It checks the list as text and, for local shard files, counts the `url` elements in each file.

## Inputs to confirm before running

| Input | Rule | If it fails |
|-------|------|-------------|
| Shard list file | UTF-8 text, at most 2 MB (working value), one shard URL per line, optional lastmod after one space; blank lines and lines starting with `#` are ignored | Exit 2 |
| `--host` | Bare host name such as `www.example.com`; no scheme, slash, or `@` | Stop and ask for the host |
| `--out` | New file name; must not exist and must not be an input path | Exit 2; pick a new name |
| `--local-shard` (optional, repeatable) | Local sitemap `urlset` XML, at most 2 MB (working value), no DTD or entity declarations in UTF-8, UTF-16 LE or UTF-16 BE, no UTF-16 or UTF-32 byte order mark, no NUL bytes | Exit 2 |

## Workflow

1. **Intake.** Confirm the shard list path, the host, the output path, and any local shard paths. Output: an input table with one row per input and a status of `ready` or `missing`. Stop if any input is missing (see Refuse / stop when).
2. **Check the output path.** Confirm the output file does not exist. Output: one line, `output path: free` or `output path: exists, choose a new name`.
3. **Run the script.** Use the command line in the script contract below. Output: the exit code and the JSON report, copied unchanged.
4. **Read the findings.** Map each finding code to the action in the code table. Output: a findings table with the columns Code, Line, Action.
5. **Check the counts.** When `status` is `written`, `entries_written` + `duplicates_dropped` + `rejected_lines` must equal `input_lines`. If the sum differs, stop and report the mismatch; do not hand over the file. Output: one line, `count check: pass` or `count check: fail`.
6. **Deliver.** Report the status, counts, local shard counts, and findings table. Do not edit the output XML by hand. If the result needs a change, fix the shard list and rerun to a new output name.

## Decision and threshold table

| Check | Threshold | Result |
|-------|-----------|--------|
| Scheme | must be `https` | `INPUT_NOT_HTTPS`, line rejected |
| Host | must equal `--host`, compared case-insensitively; a port or user part makes it differ | `HOST_MISMATCH`, line rejected |
| Duplicate | exact string match of the URL | `DUPLICATE_SHARD`, later line dropped |
| lastmod | `YYYY-MM-DD`, or W3C datetime ending in `Z` or `+hh:mm` / `-hh:mm` | `LASTMOD_INVALID`, entry kept without lastmod |
| Entries per index | more than 50,000 (published limit) | `SHARD_COUNT_OVER_LIMIT`, nothing written, exit 1 |
| URLs per local shard | more than 50,000 (published limit) | `LOCAL_SHARD_OVER_LIMIT`, index still written, exit 1 |
| No usable line | zero entries after filtering | `NO_VALID_SHARDS`, nothing written, exit 1 |
| Input and local file size | 2 MB (working value) | exit 2 |

## Finding code table

| Code | Line value | Action |
|------|------------|--------|
| `INPUT_LINE_MALFORMED` | line number | Line has more than two fields; fix the line and rerun |
| `INPUT_NOT_HTTPS` | line number | Change the URL to https; the line is not in the index |
| `HOST_MISMATCH` | line number | Remove the line or rerun with the correct `--host` |
| `DUPLICATE_SHARD` | line number of the dropped copy | Confirm the first copy has the right lastmod |
| `LASTMOD_INVALID` | line number | Correct the date; the entry is in the index without lastmod |
| `LOCAL_SHARD_OVER_LIMIT` | null | Split that shard file; the index is written but the shard is over the limit |
| `SHARD_COUNT_OVER_LIMIT` | null | Split the list across more than one index; nothing was written |
| `NO_VALID_SHARDS` | null | Fix the list; nothing was written |

## Script contract

Command line:

```
python -I scripts/sitemap_index.py --shards <input-file> --host <host> --out <output-xml> [--local-shard <shard-xml>]
```

- Arguments: `--shards` (required), `--host` (required), `--out` (required), `--local-shard` (zero or more).
- Output: one JSON object on stdout with keys `status` (`written` or `not_written`), `output_file`, `input_lines`, `entries_written`, `duplicates_dropped`, `rejected_lines`, `local_shards` (list of `file` and `url_count`), and `findings` (list of `code`, `line`, `detail`). A finding `line` is the file line number, comments included; `input_lines` counts only non-comment, non-blank lines.
- Output file: the index XML is written with exclusive-create mode. The script never overwrites a file.
- Exit codes: `0` no findings; `1` findings reported (the index may or may not be written, see `status`); `2` usage or input error, with a one-line JSON error on stderr and nothing written.

## Output contract for the delivered report

Use these headings, in this order:

- `## Result`: status, output file name, exit code.
- `## Counts`: table with columns Count and Value, one row each for `input_lines`, `entries_written`, `duplicates_dropped`, `rejected_lines`, and each local shard `url_count`.
- `## Findings`: table with columns Code, Line, Action. Write `none` if the list is empty.
- `## Open questions`: numbered list of anything the user must decide. Write `none` if there are none.

## Refuse / stop when

- `--host` is missing, or contains a scheme, a slash, or an `@`.
- The shard list or a local shard file is missing, larger than 2 MB, not UTF-8, or (for local files) not a `urlset` document.
- A local shard file contains a DTD or entity declaration in UTF-8, UTF-16 LE or UTF-16 BE form, starts with a UTF-16 or UTF-32 byte order mark, or contains a NUL byte. Local shards are checked on raw bytes before any parse.
- The output path already exists or is the same as an input path. Ask for a new name; never delete or overwrite the existing file.
- The user asks to fetch the shard URLs, check that they return a page, or submit the index to a search engine. This skill has no network access; say so and stop that step.
- The user asks to produce shard files from a page list. That is out of scope.

## Shipped files

- [scripts/sitemap_index.py](scripts/sitemap_index.py): the builder described above.
- [fixtures/shards.txt](fixtures/shards.txt): a four-line shard list with one duplicate, for a test run.
- [fixtures/local_shard.txt](fixtures/local_shard.txt): a local `urlset` XML document with three `url` elements, stored with a `.txt` name so it passes the text-only rule. The script reads the bytes the same way for any name.
- [LICENSE.txt](LICENSE.txt): the Apache-2.0 license text.

Test runs must write their output to a new file outside the fixtures folder.
