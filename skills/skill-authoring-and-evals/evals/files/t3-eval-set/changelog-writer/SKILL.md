---
name: changelog-writer
description: Writes a CHANGELOG entry from a list of merged pull requests, grouped as Added, Changed, Fixed and Removed. Use when the user asks for release notes or a changelog entry for a version. Do not use for commit message writing or marketing copy.
license: Apache-2.0
---

# Changelog writer

1. Read the merged pull request titles the user supplies.
2. Group them under Added, Changed, Fixed, Removed.
3. Write one plain line per item, newest first, with the PR number.
