# Punctuation and Capitalization Fixer

## One line

Fixes spacing, punctuation and sentence-start capitalization in a plain text file, writes a corrected copy, and lists each change with its line number.

## What it does

The script reads one UTF-8 text file of at most 2 MB and applies seven fixed rules. It deletes spaces that sit before commas, periods, semicolons, colons, exclamation marks and question marks, unless a digit comes before the space. It collapses runs of two or more spaces between words into one space. It collapses repeated commas, semicolons, colons, question marks and exclamation marks, and it shortens doubled periods. It inserts a space after a comma, semicolon or colon that sits between two letters. It inserts a space after an exclamation mark or question mark between letters, and after a period when a lowercase letter comes before it and a capitalized word follows it. It capitalizes a whole lowercase word that opens a line or follows a sentence end, and it changes a standalone lowercase i to I.

Code spans, web addresses and email addresses are masked before any rule runs, so they come out unchanged. The corrected text goes to a new file that must not exist yet, and the script never writes over its input. Each change is reported as a JSON entry with a line number, a rule code, and twelve characters of context on each side.

## When to use

Use it on pasted prose that shows the slips the rules cover: double spaces, a space before a comma or period, a missing space after a comma, a sentence that starts in lowercase, a standalone lowercase i, or doubled punctuation. It suits a case where a corrected copy is wanted together with a record of every edit, so that each edit can be checked against its line before the text is used.

## When not to use

Not for rewording, grammar, spelling, style, translation or summaries. Not for source code, log output or data files, where capitalization can carry meaning. Not for Word, PDF or spreadsheet files, which must be exported to plain text first.

## Requirements

Python 3.9 or newer, standard library only. There is no network access, no subprocess call and nothing to install. Run it with the interpreter's isolated mode flag, `python -I`.

## Example

Command run from a scratch folder, with the shipped smoke fixture as input and a new output name:

```
python -I "<workspace>/scripts/punct_fix.py" "<workspace>/fixtures/slips.txt" smoke-run.txt
```

Printed result (exit code 1):

```
{"status": "changed", "change_count": 8, "output": "smoke-run.txt", "changes": [{"line": 1, "rule": "missing_space_after", "before": "et on monday,and agreed o", "after": "et on monday, and agreed o"}, {"line": 1, "rule": "capitalize_sentence", "before": "the team met on", "after": "The team met on"}, {"line": 2, "rule": "space_before_punct", "before": "Ready?  Yes , it is done", "after": "Ready?  Yes, it is done"}, {"line": 2, "rule": "double_space", "before": "Ready?  Yes, it is d", "after": "Ready? Yes, it is d"}, {"line": 2, "rule": "repeated_punct", "before": ", it is done!!", "after": ", it is done!"}, {"line": 3, "rule": "capitalize_sentence", "before": "see https://example.com/a,b/i..x now.", "after": "See https://example.com/a,b/i..x now."}, {"line": 4, "rule": "standalone_i", "before": "day we said i was right a", "after": "day we said I was right a"}, {"line": 5, "rule": "missing_space_after_terminal", "before": "Done.Next step is", "after": "Done. Next step is"}]}
```

The web address on line 3 and the email address on line 4 are unchanged in the written file.

## Limits

The tool checks only spacing, punctuation and capitalization. It does not check meaning, grammar, spelling, facts or tone, and it does not verify that the corrected sentences read well. Capitalization covers ASCII letters only, so a sentence that opens with an accented letter is left as typed. A lowercase fragment that opens a line, such as an unbulleted list item, is capitalized like a sentence. An abbreviation outside its 22-entry set followed by a lowercase word is capitalized in error. A mixed-case token such as a filename with a lowercase letter before a capitalized part is split by a space. The 2 MB input cap and the 12-character context width are working values chosen for this tool. The tool does not check visual layout, rendering, deliverability, encoding beyond UTF-8, or security of the text it handles. It writes only the one new file, and it refuses to overwrite any existing path.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
