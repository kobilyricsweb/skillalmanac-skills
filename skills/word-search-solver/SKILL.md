---
name: word-search-solver
description: Solves a letter-grid word search from typed text. Use when a user pastes or types a word search grid with a word list and needs each word's start row, start column and direction, or needs to know which words are missing from the grid. Do not use for crossword clues, anagram or word-scramble puzzles, grids in images or PDFs that cannot be typed out, or building new word searches.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Word Search Solver

Finds each word from a list in a letter grid and reports where it starts. The grid and word list must be plain text. The script does the search; the agent prepares the files, runs the script, and reports the result.

## Workflow

1. **Intake.** Take the grid as plain text, one row per line. If the user typed letters separated by spaces, remove the spaces inside each row so that each row is one unbroken string. Required output: the row count and the column count of the grid.
2. **Save the inputs.** Write the grid to one UTF-8 text file and the word list to another, each with a file name that does not exist yet. In the word list, one word per line and no spaces inside a word. Required output: the two file names.
3. **Run the script.** Use the command in the Script contract section with the two file names. Required output: the exit code and the JSON printed to stdout (or the error line on stderr).
4. **Branch on the exit code** using the decision table below. Required output: the action taken and the message shown to the user.
5. **Verify each found word.** For each entry in `found`, read the letter at (row, col), then step by the direction's row and column deltas for the word length and read the remaining letters. Required output: "verified N of N found words" where N is the length of `found`. Any mismatch means the script result is wrong; report it and do not present the positions as correct.

## Decision table

| Exit code | `status` value | Action |
|---|---|---|
| 0 | `all_found` | Report every position in the answer format. |
| 1 | `some_not_found` | Report the found positions, list the `not_found` words, and say the missing words may be misspelled or absent from the grid. |
| 2 | (no JSON) | Show the error message from the Error messages table, ask the user to correct the input, and rerun once after the correction. Do not guess a fix. |

## Search rules

| Rule | Value |
|---|---|
| Directions searched | 8 |
| Start coordinates | 1-based; row 1 is the top row, column 1 is the left column |
| Letter case | Case-insensitive; letters are converted to upper case |
| Allowed characters | A-Z only |
| Repeat matches | Only the first match in scan order is reported: rows top to bottom, columns left to right, directions in the order below |
| Word longer than the grid | Not searched successfully; it appears in `not_found` |
| One-letter word | Matches the first cell holding that letter, direction E |
| Maximum input file size | 2 MB (working value); larger files exit 2 |
| Duplicate words in the word list | Exit 2 |

| Direction | Row delta | Column delta | Reads |
|---|---|---|---|
| E | 0 | +1 | left to right |
| W | 0 | -1 | right to left |
| S | +1 | 0 | top to bottom |
| N | -1 | 0 | bottom to top |
| SE | +1 | +1 | top-left to bottom-right |
| SW | +1 | -1 | top-right to bottom-left |
| NE | -1 | +1 | bottom-left to top-right |
| NW | -1 | -1 | bottom-right to top-left |

## Output contract

The script prints this JSON object (indented by 2 spaces) on stdout:

| Key | Type | Meaning |
|---|---|---|
| `status` | string | `all_found` or `some_not_found` |
| `rows` | integer | Grid row count |
| `cols` | integer | Grid column count |
| `found` | array | One object per found word, in word-list order |
| `found[].word` | string | Word as upper case |
| `found[].row` | integer | 1-based start row |
| `found[].col` | integer | 1-based start column |
| `found[].direction` | string | One of the 8 names in the Search rules table |
| `not_found` | array of strings | Words with no match, in word-list order |

The answer to the user uses this layout:

- A heading `## Found` followed by a table with the columns `Word`, `Row`, `Column`, `Direction`.
- A heading `## Not found` followed by a bullet list of the words, or the line `None`.
- A final line `Status: all_found` or `Status: some_not_found`.

## Error messages

Each error prints `{"error": "<message>"}` on one line to stderr and exits 2.

| Message | Cause | Fix |
|---|---|---|
| `usage: wordsearch.py <grid-file> <word-file>` | Wrong number of arguments | Pass exactly two file names. |
| `cannot read grid file` / `cannot read word file` | Missing file or unreadable path | Check the file name and location. |
| `grid file exceeds 2 MB` / `word file exceeds 2 MB` | File over the size limit | Stop; ask the user for a smaller input. |
| `grid file is not valid UTF-8` / `word file is not valid UTF-8` | Non-UTF-8 encoding | Save the file again as UTF-8. |
| `grid is empty` | No non-blank rows | Ask the user for the grid. |
| `ragged grid: every row must have the same length` | Rows of different lengths | Ask the user to re-enter the grid; do not pad rows. |
| `grid contains characters other than A-Z` | Digits, punctuation, accents or non-Latin letters | Ask the user to confirm the letters. |
| `word list contains characters other than A-Z` | Spaces inside a word or non-Latin letters | Split phrases or ask the user to correct the list. |
| `duplicate word in word list` | The same word appears twice | Remove the duplicate and rerun. |
| `word list is empty` | No non-blank lines | Ask the user for the word list. |

## Script contract

- Script: `scripts/wordsearch.py`
- Arguments: argv[1] is the grid file; argv[2] is the word file. No options.
- Output keys: see the Output contract table.
- Exit codes: 0 all words found; 1 one or more words not found; 2 usage or input error.
- Writes: nothing. Input files are read only.
- Command line: `python -I scripts/wordsearch.py <grid-file> <word-file>`

## Refuse / stop when

- The grid exists only as an image, scan, photo or PDF that the user cannot type out.
- Rows of the grid differ in length. Do not pad rows with guessed letters.
- The grid or word list contains characters outside A-Z, such as accents, digits, punctuation or non-Latin letters.
- A word list entry is a phrase with spaces, or a word appears twice.
- An input file is larger than 2 MB.
- The user asks to fill in missing letters, generate a new grid, or solve a clue-based puzzle.
- Any step would overwrite a file the user supplied or an earlier result file.

## Shipped files

- `scripts/wordsearch.py`: the solver.
- `fixtures/grid_6x6.txt` and `fixtures/words_5.txt`: the smoke-test grid and word list (4 words found, 1 not found, exit 1).
- `fixtures/grid_ragged.txt`: a grid with a short row, used to check the exit 2 path.
- `LICENSE.txt`: Apache-2.0 license text.
