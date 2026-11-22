# Keyword density count

## One line

Counts whole-word keyword matches and density percentages in one page's plain text, then lists the top terms and bigrams.

## What it does

The skill takes a page's visible text and a list of target keywords, one per line. A bundled Python script (standard library only) lowercases the text, splits it into word tokens, and counts every occurrence of each keyword as a whole-token sequence. Each keyword gets a density percentage computed as matches times the phrase's word count, divided by the total word count of the page. The script also ranks the 15 most frequent non-stopword single words and the 15 most frequent bigrams where neither word is a stopword. Any keyword with zero matches is flagged ABSENT and the process exits with code 1. The output is a JSON object; the skill turns it into a fixed report with a counts table, an absent list, two top lists and the note that no density value is a ranking target. The script reads two files and writes nothing.

## When to use

Use it when a draft page is being checked by eye and the editor wants repeatable numbers: the same text, the same keyword file, the same counts on every rerun. It fits a before-publish pass on one page, or a comparison of two revisions of that page, where the question is whether the target phrases are present at all and how often they appear relative to length.

## When not to use

Do not use it to predict search rankings, to set a density goal, or to judge keyword stuffing with a percentage cutoff. The script has no pass mark and the skill refuses to invent one. Do not use it on HTML or on a rendered page, because tags and scripts would be counted as words. It does not match synonyms, plurals or related phrases unless each form is listed as its own keyword.

## Requirements

Python 3.9 or newer, with the standard library only. No network access and no packages to install. Both input files must be UTF-8, the page text at most 2 MB and the keyword file at most 2 MB, with no more than 100 keywords of 10 words or fewer each.

## Example

Command run from the skill folder against the bundled 300-word fixture and its three-keyword list. Exit code 1 because `backlinks` does not occur in the text.

```
{
  "total_words": 300,
  "keywords": [
    {
      "keyword": "keyword density",
      "words": 2,
      "matches": 6,
      "density_pct": 4.0,
      "status": "FOUND"
    },
    {
      "keyword": "page",
      "words": 1,
      "matches": 10,
      "density_pct": 3.33,
      "status": "FOUND"
    },
    {
      "keyword": "backlinks",
      "words": 1,
      "matches": 0,
      "density_pct": 0.0,
      "status": "ABSENT"
    }
  ],
  "absent_keywords": [
    "backlinks"
  ],
  "top_terms": [
    {
      "term": "page",
      "matches": 10,
      "density_pct": 3.33
    },
    {
      "term": "density",
      "matches": 9,
      "density_pct": 3.0
    },
    {
      "term": "keyword",
      "matches": 8,
      "density_pct": 2.67
    },
    {
      "term": "text",
      "matches": 6,
      "density_pct": 2.0
    },
    {
      "term": "count",
      "matches": 4,
      "density_pct": 1.33
    },
    {
      "term": "list",
      "matches": 4,
      "density_pct": 1.33
    },
    {
      "term": "same",
      "matches": 4,
      "density_pct": 1.33
    },
    {
      "term": "one",
      "matches": 3,
      "density_pct": 1.0
    },
    {
      "term": "only",
      "matches": 3,
      "density_pct": 1.0
    },
    {
      "term": "phrase",
      "matches": 3,
      "density_pct": 1.0
    },
    {
      "term": "absent",
      "matches": 2,
      "density_pct": 0.67
    },
    {
      "term": "case",
      "matches": 2,
      "density_pct": 0.67
    },
    {
      "term": "check",
      "matches": 2,
      "density_pct": 0.67
    },
    {
      "term": "draft",
      "matches": 2,
      "density_pct": 0.67
    },
    {
      "term": "how",
      "matches": 2,
      "density_pct": 0.67
    }
  ],
  "top_bigrams": [
    {
      "term": "keyword density",
      "matches": 6,
      "density_pct": 4.0
    },
    {
      "term": "page text",
      "matches": 2,
      "density_pct": 1.33
    },
    {
      "term": "absent keywords",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "absent list",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "another page",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "answer quickly",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "applies before",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "case applies",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "case insensitive",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "category sometimes",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "change anything",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "check counts",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "compare revisions",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "counts how",
      "matches": 1,
      "density_pct": 0.67
    },
    {
      "term": "decision next",
      "matches": 1,
      "density_pct": 0.67
    }
  ],
  "note": "Density is descriptive only. No density value is a ranking target."
}
```

## Limits

The counts are token counts over plain text. The script does not parse HTML, so markup must be removed before the run. Its tokenizer keeps only ASCII letters and digits, so accented letters and curly apostrophes split a word. Matches overlap and can cross a sentence or paragraph break: in the example, the sixth `keyword density` match spans the end of one paragraph and the start of the next. Top lists use a fixed 68-word stopword list in English and do not stem words. The tool does not check spelling, grammar, readability, duplicate content, anchor text, metadata, or whether the page would rank for any query.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
