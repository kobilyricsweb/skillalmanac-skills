# Word Search Solver

## One line

Finds each listed word in a letter grid and reports its 1-based start row, start column and direction, or marks it as not found.

## What it does

The skill takes a letter grid typed as plain text, one row per line, and a word list typed as one word per line. A bundled Python script searches each word in all 8 directions: east, west, south, north and the four diagonals. It scans the grid from the top-left cell and reports the first match it finds for each word, so a word that appears twice gets only its earlier position. Each found word comes back with its row, its column and the direction it reads. Words that never appear are listed separately.

The script reads its two input files and writes nothing. It rejects grids whose rows differ in length, grids and word lists containing anything other than the letters A to Z, duplicate words, and files larger than 2 MB, and it names the problem in a one-line error message. The agent then reports the result as a table of found words, a list of missing words and a final status line.

## When to use

Use it when someone has a word search that is typed out, or copied from a page as text, and wants the positions of the words checked, or wants to confirm which listed words are missing from the grid.

## When not to use

Do not use it for crossword clues, anagram or word-scramble puzzles, or puzzles that only exist as an image, a scan or a PDF that cannot be retyped. It does not fill in unreadable letters, does not build new word searches, and does not handle accented, Hebrew, Cyrillic or other non-Latin letters.

## Requirements

Python 3.9 or later on the system path, using only the standard library. No network access, no packages to install and no write access beyond the agent's working folder.

## Example

Command: `python -I scripts/wordsearch.py fixtures/grid_6x6.txt fixtures/words_5.txt`

Output (exit code 1):

```json
{
  "status": "some_not_found",
  "rows": 6,
  "cols": 6,
  "found": [
    {
      "word": "CAT",
      "row": 1,
      "col": 1,
      "direction": "E"
    },
    {
      "word": "DOG",
      "row": 2,
      "col": 2,
      "direction": "SE"
    },
    {
      "word": "WIRE",
      "row": 3,
      "col": 6,
      "direction": "S"
    },
    {
      "word": "LAMP",
      "row": 6,
      "col": 4,
      "direction": "W"
    }
  ],
  "not_found": [
    "ZEBRA"
  ]
}
```

## Limits

- Letters A to Z only, with no spaces inside a word and no punctuation.
- Input files are capped at 2 MB (working value).
- Only the first match of each word is reported, in row-then-column scan order.
- A word longer than the grid cannot be found and appears under not found.
- The script does not check whether a word is a real dictionary word or whether a puzzle has a single intended answer.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
