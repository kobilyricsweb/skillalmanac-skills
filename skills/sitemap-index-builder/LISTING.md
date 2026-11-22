# Sitemap index builder

## One line

Builds one sitemap index XML file from a list of shard URLs, after checking scheme, host, duplicates, lastmod format, and the 50,000 entry and URL limits.

## What it does

The skill runs a standard-library Python script over a plain text list of shard URLs. Each line may carry an optional lastmod date after one space. The script rejects any line that is not https or whose host differs from the host given on the command line. It drops later copies of an exact duplicate URL, keeps a lastmod only when it matches the date or W3C datetime pattern, and writes the surviving entries as a new sitemap index file. The file is created with exclusive-create mode, so an existing file is never replaced.

If local shard files are supplied, the script counts the url elements in each one and flags any file above 50,000. It reads each shard as bytes and refuses DTD and entity declarations in UTF-8, UTF-16 LE, and UTF-16 BE forms, refuses UTF-16 and UTF-32 byte order marks and NUL bytes, and confirms the root element is urlset. It prints one JSON report that gives counts, per-shard totals, and a finding list with a code, line number, and fixed detail text for each problem. The `line` value in a finding is the file line number, comments included; `input_lines` counts only non-comment, non-blank lines. The agent then turns that report into a short table for the user. Exit codes separate a clean run, a run with findings, and a usage or input error.

## When to use

Use this skill when a site has grown past one sitemap file and the shard files already exist or are about to be published. It is useful when someone has a list of shard URLs in a spreadsheet export or a generator log and needs a clean index with the duplicates removed and the host checked. It is also useful when a small local shard has been rebuilt and the count needs confirming against the 50,000 URL limit before the index is published.

## When not to use

Do not use it to generate the shard files, to crawl a site for URLs, or to fetch the shard URLs and confirm they answer. The script has no network access. Do not use it to submit the index to a search engine, to rename or move published files, or to build a urlset from a page list. A site with a single sitemap file does not need an index.

## Requirements

Python 3.9 or later, standard library only. No network access, no subprocess calls. The shard list and each local shard file must be UTF-8 text (no UTF-16 or UTF-32), at most 2 MB each. The output path must not exist. Run the command from the skill folder, or pass full paths.

## Example

Run on the shipped fixture: four shard lines with one exact duplicate, and one local shard with three url elements. The output file went to a scratch folder.

```
{
  "status": "written",
  "output_file": "sitemap_index_run3.xml",
  "input_lines": 4,
  "entries_written": 3,
  "duplicates_dropped": 1,
  "rejected_lines": 0,
  "local_shards": [
    {
      "file": "local_shard.txt",
      "url_count": 3
    }
  ],
  "findings": [
    {
      "code": "DUPLICATE_SHARD",
      "line": 5,
      "detail": "URL already listed earlier; line dropped"
    }
  ]
}
```

The counts reconcile: 3 entries written, plus 1 duplicate dropped, plus 0 rejected lines, equals the 4 input lines. The exit code is 1 because a finding was reported.

Refusal check: a UTF-16 LE local shard with a DOCTYPE and an ENTITY declaration, built at runtime in the scratch folder, is refused before any parse. Nothing is written and the exit code is 2:

```
{"error": "DTD or entity declaration refused: hostile_utf16.txt"}
```

## Limits

A local shard over 2 MB is refused with exit 2, so a full 50,000-URL shard (typically 3 to 10 MB) cannot be counted here; use this check only for small shards, or count `<url>` elements another way. The script does not fetch shard URLs, so it cannot confirm that they return a page or that they are reachable. It does not check the 50 MB uncompressed size limit of a shard file, and it does not compare the lastmod values with the file contents. Duplicates are exact string matches, so a URL that differs only by case or by a trailing slash is not flagged. The lastmod check confirms the pattern and date range but not the time-of-day range. The tool does not verify that any search engine accepts or indexes the result, and it does not judge whether the shard split is a good one.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
