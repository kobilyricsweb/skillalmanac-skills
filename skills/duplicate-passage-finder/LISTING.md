# Duplicate Passage Finder

## One line

Finds paragraphs that repeat, exactly or nearly, across a folder of plain-text and Markdown files, with the file and line of every copy.

## What it does

The script walks one folder, including its subfolders, and reads every .txt and .md file as UTF-8. It splits each file into paragraphs at blank lines and collapses whitespace and letter case so that line breaks and capitalization do not hide a repeat. Paragraphs shorter than 8 words are skipped and counted, so short headings and sign-offs never appear as groups.

Exact copies are grouped first. For near copies, each paragraph is turned into 8-word shingles and two paragraphs are linked when their shingle sets have a Jaccard similarity of 0.6 or higher. Linked paragraphs form one group, so a paragraph that is close to two others still appears once in a group with all three locations. The output is a JSON report with a group ID, a type of exact or near, and a file and line for each occurrence, plus summary counts. The script reads only and writes nothing.

## When to use

Use it when a set of drafts, memos, or notes has grown by copying, and someone needs to know which paragraphs now appear in several places before merging, archiving, or editing. It is useful when the folder holds many small files and checking them by hand would take longer than the review itself.

## When not to use

Do not use it to compare two files line by line, to find repeated single sentences, or to read .docx, .pdf, or .html content. Do not use it to delete or rewrite repeats; it only reports them. It is also the wrong tool when meaning, not wording, is the question, because paraphrases are not matched unless their word sequences overlap.

## Requirements

Python 3.9 or later, standard library only. No network access, no subprocess calls, and no installed packages. The input folder must be readable, and the total size of the .txt and .md files must not exceed 2 MB.

## Example

Command run on the bundled fixture folder, which has four files and one exact and one near repeated paragraph:

```
python -I scripts/dup_passages.py fixtures/docs
```

Output (exit code 1, meaning groups were found):

```
{
  "settings": {
    "min_words": 8,
    "shingle_size": 8,
    "jaccard_threshold": 0.6
  },
  "files_scanned": 4,
  "paragraphs_compared": 8,
  "paragraphs_skipped_short": 5,
  "groups": [
    {
      "group_id": "G1",
      "type": "exact",
      "occurrences": [
        {
          "file": "a_q3_summary.md",
          "line": 3
        },
        {
          "file": "b_field_notes.txt",
          "line": 5
        }
      ]
    },
    {
      "group_id": "G2",
      "type": "near",
      "occurrences": [
        {
          "file": "c_audit_memo.md",
          "line": 3
        },
        {
          "file": "d_audit_memo_copy.txt",
          "line": 3
        }
      ]
    }
  ],
  "counts": {
    "groups": 2,
    "exact_groups": 1,
    "near_groups": 1,
    "occurrences": 4
  }
}
```

## Limits

The script does not judge meaning, so a repeated boilerplate notice is reported the same way as a repeated argument. It does not match paraphrases that share few word sequences, and it does not look inside tables, code blocks, or front matter as structure; those are read as plain text. It compares only paragraphs of 8 words or more. The 0.6 threshold, 8-word minimum, and 8-word shingles are working values chosen for this skill, not published standards, and they have been tested on one small fixture only. The script does not verify that the files are current, authorized, or the right versions, and it does not check file names or metadata beyond the extension.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
