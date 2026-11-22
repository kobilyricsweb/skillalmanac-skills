# Flashcard Set Builder

## One line

Turns a plain text list of term and definition lines into a deduplicated front,back CSV and marks the cards that need editing.

## What it does

The skill runs one Python script over a notes file that holds one card per line. Each line is split at its double colon into a front and a back. The script then walks the lines in order and drops any card whose front and back match an earlier kept card exactly, or whose front shares more than 0.8 of its word set with an earlier kept front. Cards that survive are checked for long fronts (more than 12 words), long backs (more than 30 words), and definitions that repeat their own term as a whole word. Flagged cards stay in the output; only duplicates are removed. The script writes a new CSV with a front,back header and prints a short count summary with one line for each drop and each flag, so the author can see exactly which input lines to revisit.

## When to use

Use it when a student or teacher has accumulated notes in term-and-definition form and the deck has grown with repeats, or when a card set needs a quick quality pass before import into a flashcard app. It suits a list of a few dozen to a few thousand cards that already exists as text.

## When not to use

Do not use it to write or improve card wording, to generate questions from a textbook, to schedule reviews, or to convert slides or PDFs into notes. It does not judge whether a definition is correct.

## Requirements

Python 3.9 or later, standard library only. No network access and no packages to install. The input must be UTF-8 text, at most 2 MB.

## Example

Run on the shipped sample of twelve lines with two repeats, one long back, one definition that repeats its term, and one long front:

```
lines=12 blank=0 cards=12
kept=10 dropped=2 flags=3
DROP line=3 code=DUP_EXACT duplicate_of_line=1
DROP line=5 code=DUP_NEAR duplicate_of_line=4
FLAG line=6 code=BACK_LONG
FLAG line=7 code=DEF_CONTAINS_TERM
FLAG line=12 code=FRONT_LONG
written=out_listing.csv
result=findings
```

## Limits

Duplicate detection works on words, not meaning. Two cards that define the same idea in different words will both survive. Word order does not matter for the near check, so a reordered front can be dropped. The term check compares whole tokens only, so "cell" does not match "cells". The 12-word and 30-word limits and the 0.8 overlap value are working values chosen for this skill and are not a published standard. The script caps input at 2 MB and 5000 cards, and it refuses to overwrite an existing output file.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
