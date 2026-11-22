---
name: good-skill
description: Writes a CHANGELOG entry from a list of merged pull requests, grouped as Added, Changed, Fixed and Removed. Use when the user asks for release notes, a changelog entry or what changed in a version. Do not use for commit message writing or marketing copy.
license: Apache-2.0
metadata:
  author: fixture
  version: "0.1.0"
  network: none
---

# Good skill

Groups merged pull requests into a changelog entry.

## Workflow

1. Read the pull request titles the user supplies.
2. Group them under Added, Changed, Fixed, Removed.
3. Write one plain line per item with the PR number.

## Limits

- Needs the titles; it does not fetch them.
