---
name: tidy-csv-summary
description: Summarises a CSV file into row count, column names and per-column empty counts using a bundled script. Use when the user asks for a quick profile of a CSV. Do not use for Excel files or for cleaning data.
license: Apache-2.0
metadata:
  author: Example Author
  version: "1.0.0"
  network: none
---

# Tidy CSV summary

1. Run `python scripts/summarize.py <file.csv>`.
2. Report the printed JSON to the user.

The script only reads the file you give it and prints to the terminal.
