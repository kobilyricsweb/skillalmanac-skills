# Stock Phrase Scanner

## One line

Counts stock filler phrases, hedges and repeated sentence openers in a plain-text draft and reports the line numbers for each.

## What it does

The scanner reads one UTF-8 text file and checks it against a fixed list of 50 phrases. Forty-one entries are filler, such as "delve into" or "in order to", and nine are hedges, such as "arguably" or "could potentially". Matching ignores case, requires whole-word boundaries, and treats curly apostrophes as straight ones. For every phrase it finds, the output gives the total count and each line where the phrase appears.

A second check looks at sentence openers. The script takes the first two words of each sentence, splits sentences at a period, exclamation mark or question mark followed by whitespace, and flags any opener that appears three or more times. Each flagged opener is listed with its count and line numbers, so an author can see which paragraph is leaning on the same sentence start.

The output also gives words, lines, total phrase hits, and hits per 1,000 words. The script never labels authorship and never rewrites text. It writes nothing to disk and opens no network connection.

## When to use

- A draft reads as generic and the author wants to locate the exact lines that carry stock phrasing.
- An editor wants a repeatable count of hedges before a review pass, so that the same draft gives the same numbers on each run.
- A writer is checking a section for repeated openers such as "the team" or "it is" at the start of several sentences in a row.

## When not to use

- The question is whether a person or an AI tool wrote the text. The counts cannot answer that.
- The task is to rewrite, paraphrase or polish sentences. The scanner reports; it does not edit.
- The file is a spreadsheet, a PDF, a Word document or a binary export. Convert it to plain text first.
- The task is grammar, spelling, reading level or style beyond the listed phrases.

## Requirements

- Python 3.9 or later. Standard library only.
- No network access and no third-party packages.
- Input: one UTF-8 text file of 2 MB or less. A byte order mark is accepted.

## Example

Command run against the shipped smoke-test draft:

```
python -I scripts/phrase_scan.py fixtures/draft_sample.txt
```

Output, exit code 1:

```
{
  "file": "draft_sample.txt",
  "words": 210,
  "lines": 14,
  "phrase_hit_total": 5,
  "hits_per_1000_words": 23.81,
  "phrase_hits": [
    {
      "phrase": "delve into",
      "category": "filler",
      "count": 1,
      "lines": [
        6
      ]
    },
    {
      "phrase": "it's important to note",
      "category": "filler",
      "count": 1,
      "lines": [
        7
      ]
    },
    {
      "phrase": "at the end of the day",
      "category": "filler",
      "count": 1,
      "lines": [
        12
      ]
    },
    {
      "phrase": "in order to",
      "category": "filler",
      "count": 1,
      "lines": [
        8
      ]
    },
    {
      "phrase": "a testament to",
      "category": "filler",
      "count": 1,
      "lines": [
        13
      ]
    }
  ],
  "opener_repeats": [
    {
      "opener": "engineering will",
      "count": 3,
      "lines": [
        8,
        13,
        14
      ]
    },
    {
      "opener": "refund requests",
      "count": 3,
      "lines": [
        9,
        10,
        11
      ]
    },
    {
      "opener": "the team",
      "count": 3,
      "lines": [
        3,
        4,
        5
      ]
    }
  ],
  "finding_count": 8
}
```

## Limits

- The phrase list is a working list, not a published standard. Phrases were chosen for common stock wording and may miss other stock wording or flag ordinary usage in a specialized text.
- Sentences are split only at a period, exclamation mark or question mark inside a single line. A sentence broken across two lines without punctuation is counted from the line where it starts.
- Openers use the first two words only. Two sentences that start with "The team" and "The teams" are counted as different openers.
- Density is a simple ratio. It does not adjust for quotations, code blocks or headings.
- The scanner has no notion of meaning, so a hedge inside a quotation is still counted.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
