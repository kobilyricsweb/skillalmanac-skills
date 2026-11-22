# text-redline-diff

## One line

Compares two plain-text or Markdown drafts paragraph by paragraph and word by word, and prints the changes inline as [-deleted-] and [+inserted+] markers.

## What it does

The script splits each file into paragraphs at blank lines, aligns the two paragraph lists with a sequence matcher, and pairs replaced paragraphs when their words are at least half alike. Paired paragraphs get an inline word diff. Unpaired paragraphs are reported as inserted or deleted as a whole. A removed paragraph whose exact text reappears elsewhere in the new file is reported as moved and is not counted as a deletion. The output ends with paragraph counts and word counts, so a reviewer can check the totals against the two files. Default comparison is case-sensitive and whitespace-strict. Two flags relax either rule. An optional report file receives the same text, and it is created only if the name is new.

## When to use

Use it when a reviewer needs to see exactly which words changed between two drafts of a memo, policy, article, or specification that already exists as text or Markdown. It suits a short review pass before a sign-off, where the reviewer wants both the changed sentence and the exact changed words.

## When not to use

Do not use it for Word, PDF, or spreadsheet files, which must be exported to text first. Do not use it to decide whether a change is correct, lawful, or accurate. It also does not compare by sentence or by page, and it does not follow tracked changes or comments already present in a document.

## Requirements

Python 3.9 or later, standard library only. No network access and no subprocess calls. Each input file must be UTF-8 text and at most 2 MB.

## Example

Command run on the two fixture files shipped with the skill:

```
python -I scripts/redline.py fixtures/old_version.txt fixtures/new_version.txt
```

Output (exit code 1):

```
# Redline
old: old_version.txt
new: new_version.txt
flags: case=sensitive whitespace=strict
paragraphs: old=12 new=12
paragraph_counts: changed=3 inserted=1 deleted=1 moved=0 whitespace_only=0 unchanged=8
word_counts: inserted=17 deleted=10

## Changed: old P2 -> new P2
The pilot began in [-March-] [+April+] and covered three warehouses.

## Changed: old P5 -> new P5
The main risk is delayed delivery of replacement [+handheld+] scanners.

## Deleted: old P8
[-Two warehouses reported minor problems with label printers.-]

## Changed: old P10 -> new P9
Feedback from [+the+] floor supervisors has been [-mostly-] [+very+] positive.

## Inserted: new P11
[+A closing review will be held at the end of the second quarter.+]
```

## Limits

The tool compares text only. It does not see layout, fonts, images, tables, footnotes, or comments, so it cannot confirm visual equality of two rendered pages. It does not verify facts, meaning, tone, or legal effect of a change. Paragraph pairing uses a fixed similarity threshold of 0.5, which is a working value and can pair or split paragraphs differently than a human editor would. Inline output joins words with single spaces, so line breaks inside a changed paragraph are not shown. The script does not check file ownership, deliverability, or security of the inputs.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
