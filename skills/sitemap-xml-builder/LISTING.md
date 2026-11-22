# sitemap-xml-builder

## One line

Turns a plain list of page URLs into a sitemap.xml file and flags the entries that would break the sitemap protocol.

## What it does

The script reads a text file with one page URL per line, optionally followed by a lastmod date. It checks each line in a fixed order: line shape, URL form, fragments, length, date format, scheme, host, and duplicates. The first copy of a repeated page is kept. Every excluded line receives a single code, so the person can see which line failed and why.

The script then writes a new sitemap file containing the kept entries, with ampersands and angle brackets escaped. It prints one JSON summary line with counts for each code. Nothing is fetched, so a page that returns an error will still be listed as valid; the tool checks the list, not the site.

## When to use

Use it when someone has a list of URLs from a spreadsheet, a crawl export, or a content plan and needs a sitemap file quickly. It also fits a hand-written sitemap that has grown by copy and paste, where duplicates, stray fragments, and a leftover http entry are common.

## When not to use

Do not use it to test whether pages load, to read a live site, to submit a file to a search console, or to build a sitemap index for more than 50,000 URLs. The script never overwrites a file, so a rerun needs a new output name.

## Requirements

Python 3.9 or newer, standard library only. No network access and no other programs are started. The input file must be UTF-8 text no larger than 2 MB.

## Example

Command, run from the skill folder with the shipped ten-line fixture and a new output file name:

```
python -I scripts/sitemap_build.py fixtures/sample_urls.txt <output-file>
```

Real stdout from that run (exit code 1):

```
{"status":"findings","entries":10,"urls_written":7,"reference_scheme":"https","reference_host":"example.com","counts":{"BAD_LINE":0,"INVALID_URL":0,"FRAGMENT":1,"TOO_LONG":0,"BAD_LASTMOD":0,"MIXED_SCHEME":1,"HOST_MISMATCH":0,"DUPLICATE":1},"excluded":[{"line":3,"code":"DUPLICATE"},{"line":5,"code":"FRAGMENT"},{"line":6,"code":"MIXED_SCHEME"}]}
```

Seven entries reached the sitemap file. Line 3 repeats line 2 once the trailing slash is ignored, line 5 carries a hash fragment, and line 6 is the only http entry among https entries.

## Limits

The script does not fetch pages, check status codes, read robots rules, or confirm that a canonical tag matches. It does not judge whether a URL is the right one for search. Scheme and host choice follow the majority of the list, which may not match the owner's intent when the list is evenly split. Only the first failing check is reported per line. The 2 MB input cap and the tie rules are working values, not published limits.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
