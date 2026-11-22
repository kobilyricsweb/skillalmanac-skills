---
name: sitemap-xml-builder
description: Builds a valid sitemap.xml from a plain list of page URLs and reports every entry that breaks the sitemap protocol. Use when a user has a list of page URLs and needs a sitemap file, or when a hand-written sitemap needs checking for duplicates, fragments, mixed http and https, or host mismatches. Do not use for fetching pages, checking HTTP status codes, reading a live site, submitting sitemaps to search engines, or building sitemap index files.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Sitemap XML Builder

This skill turns a plain text list of page URLs into one sitemap file. The script
does the checks and the writing. The agent prepares the input file, runs the
script, explains each excluded line, and reports the result. The script never
fetches a URL, so it cannot tell whether a page exists or returns a 200.

## Workflow

1. **Intake.** Required fact: the list of URLs. Output: the count of non-blank
   lines the user supplied. If the list is missing, stop and use the stop rule below.
2. **Write the input file.** Save the list as UTF-8 text in a new `.txt` file,
   one URL per line. A line may carry one optional lastmod date after a space or
   tab. Output: the input file path and its entry count.
3. **Run the script** with the command in the Script contract section. Output:
   the one-line JSON summary and the exit code (0, 1 or 2).
4. **Explain the exit.** Exit 0: every entry is in the sitemap. Exit 1: the
   sitemap holds only the kept entries; each excluded line needs a fix. Exit 2:
   nothing was written; fix the error code named in the error table. Output: the
   status line of the report.
5. **Map each excluded line** to its fix in the Finding codes table. Output: one
   row per excluded line in the excluded table of the report.
6. **Re-run only on a corrected input, to a new output file name.** Never
   overwrite. Output: the second summary, labeled as a re-run.
7. **Report** with the output contract below.

## Decision and threshold table

| Check | Value | Source | Result when crossed |
|---|---|---|---|
| URLs per sitemap file | 50,000 | published protocol limit | exit 2, URL_LIMIT_EXCEEDED; split the list |
| Uncompressed file size | 52,428,800 bytes (50 MB) | published protocol limit | exit 2, SIZE_LIMIT_EXCEEDED |
| Characters per URL | 2,048 | published protocol limit | that line excluded, TOO_LONG |
| Input file size | 2,097,152 bytes (2 MB) | working value | exit 2, INPUT_TOO_LARGE |
| Reference scheme | scheme used by more entries; a tie goes to https | working value | other scheme excluded, MIXED_SCHEME |
| Reference host | host used by most reference-scheme entries; a tie goes to the host seen first | working value | other hosts excluded, HOST_MISMATCH |
| Lastmod format | YYYY-MM-DD, or a W3C datetime with hour and minute | published protocol format | that line excluded, BAD_LASTMOD |

The script compares hosts case-insensitively and treats a trailing slash on the
path as the same page. The query string is compared exactly.

## Finding codes

Each excluded line gets exactly one code, the first check it fails in this order:
BAD_LINE, INVALID_URL, FRAGMENT, TOO_LONG, BAD_LASTMOD, MIXED_SCHEME, HOST_MISMATCH,
DUPLICATE. The first copy of a duplicate stays in the sitemap.

| Code | Triggered when | Fix to suggest |
|---|---|---|
| BAD_LINE | the line has more than two fields | keep one URL, then at most one lastmod date |
| INVALID_URL | not http or https, no host, user name in the host part, a space or control character, or non-ASCII text | percent-encode the URL and use http or https with a host |
| FRAGMENT | the URL contains a hash sign | remove the part from the hash sign on |
| TOO_LONG | more than 2,048 characters | shorten the URL or move parameters out |
| BAD_LASTMOD | the date is not a real date in the accepted format | write YYYY-MM-DD, for example 2026-10-01 |
| MIXED_SCHEME | the scheme is the minority scheme in the list | use one scheme for the whole sitemap |
| HOST_MISMATCH | the host differs from the reference host | keep one host per sitemap file |
| DUPLICATE | same host, same path without trailing slash, same query as an earlier kept line; a later copy's lastmod is discarded and the first copy's lastmod (or none) is kept | delete one of the two lines |

## Output contract

The script prints one JSON line to stdout on exit 0 or 1 with these keys, in this order:
`status` (ok or findings), `entries`, `urls_written`, `reference_scheme`,
`reference_host`, `counts` (one key for each of the eight finding codes, zero when
absent), and `excluded` (a list of objects with `line` and `code`).

The file written is an XML document with an XML declaration, one `urlset` root in
the sitemap namespace, and one `url` element per kept entry holding `loc` and, when
supplied, `lastmod`. Ampersands, less-than and greater-than signs are escaped. Entries keep their input order.

The agent's report uses these headings, in this order:

```
## Sitemap result
Status: ok | findings | error
Entries read: <entries>; URLs written: <urls_written>
Reference scheme: <reference_scheme>; reference host: <reference_host>

## Excluded lines
| Line | Code | Fix |
(one row per excluded line; write "None" when the list is empty)

## Open questions
(numbered list; write "None" when empty)
```

## Refuse or stop when

- No URL list was given. Stop and ask: 1. Paste the page URLs, one per line. 2. Add a lastmod date to any line you have one for.
- The list is over 50,000 kept URLs or over 2 MB. Stop and suggest splitting the list into several files; a sitemap index is outside this skill.
- The user asks to overwrite an existing sitemap file. Refuse that clause and name a new file.
- The user asks to fetch pages, check status codes, or confirm pages are live. Refuse that clause, keep the rest of the sitemap, set Status to findings and list the request under Open questions.
- The user asks to submit the sitemap to a search engine or ping one. Refuse that clause the same way.
- URLs carry session tokens, passwords, or personal identifiers in the query string. Stop and ask the user to remove them before any public sitemap is written.

## Script contract

Script: [scripts/sitemap_build.py](scripts/sitemap_build.py)

Arguments: `<input-file>` is an existing UTF-8 text file of at most 2 MB (a leading
byte order mark is accepted). `<output-file>` is a path that must not exist.

Command line, run from the skill folder:

```
python -I scripts/sitemap_build.py <input-file> <output-file>
```

Exit codes: 0 every entry written. 1 some entries excluded, output written. 2 usage
or input error, nothing written.

Errors arrive on stderr as one JSON line with keys `error` and `message`. The error codes are:

| Error code | Meaning |
|---|---|
| USAGE | wrong number of arguments |
| FILE_NOT_FOUND | input path does not exist |
| INPUT_READ_ERROR | input cannot be opened or read |
| INPUT_TOO_LARGE | input is over 2 MB |
| INVALID_UTF8 | input is not valid UTF-8 |
| NO_ENTRIES | input has no URL lines |
| NO_VALID_URLS | no usable URL, or every line was excluded |
| URL_LIMIT_EXCEEDED | more than 50,000 kept URLs |
| SIZE_LIMIT_EXCEEDED | output would be over 50 MB |
| OUTPUT_EXISTS | output path already exists |
| OUTPUT_WRITE_ERROR | output file cannot be created |

## Shipped files

- [scripts/sitemap_build.py](scripts/sitemap_build.py): the builder and checker.
- [fixtures/sample_urls.txt](fixtures/sample_urls.txt): ten lines with one duplicate, one fragment and one http entry among https entries, for a smoke run.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0 text.
