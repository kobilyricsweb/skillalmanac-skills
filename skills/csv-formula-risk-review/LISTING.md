# CSV Formula Risk Review

Find formula-like cells in a CSV before handing an export to another team. The report gives record and column locations without exposing cell values or modifying the file.

- Category: Security / Data & Analytics.
- Intended user: an operations analyst, support export owner or developer reviewing a customer-facing CSV export.
- Useful search phrases: CSV formula injection check; Excel CSV export safety; spreadsheet formula risk; CSV injection scanner.
- Source and copyright holder: Global Media Holdings. Apache-2.0.
- Authorship: drafted with Codex assistance. One independent Claude Haiku 5.5 static critique was reviewed; empty-input, field-size and scope wording findings were fixed and checked locally. No human review or measured efficacy uplift is claimed.
- Local validation: 20 synthetic behavioral checks passed, plus Codex skill frontmatter validation. Includes malformed CSV, UTF-8 failure, BOM-only input, full-width indicators, multiline location, tab delimiters and file-preservation checks. Spreadsheet applications were not executed.
- Limits: indicator review only. Legitimate negative numbers and handles can be flagged. Import behavior depends on the recipient's application and settings. No universal sanitization or safety certification.

Example request: “Review this UTF-8 customer export before I share it. Locate formula-like cells, keep the original unchanged, and explain what needs manual review.”

This is a real original contribution prepared during an owner-authorized contributor-flow audit. Any QA comments about site mechanics are identified separately from genuine skill-use feedback.
