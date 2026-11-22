Facts used, restated in our own words. The URLs were not re-fetched while authoring this package; check them when reviewing.

- Michael Nygard, "Documenting Architecture Decisions" (15 November 2011), https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions . Origin of the short record with title, status, context, decision and consequences. It proposes numbered records kept with the code, and recording a changed decision as a new record that supersedes the old one rather than editing history.
- ADR community site, https://adr.github.io/ . Overview of the practice and of the template families, including MADR (Markdown Architectural Decision Records). MADR names its sections "Context and Problem Statement", "Considered Options", "Decision Outcome" and "Consequences"; the scanner accepts those headings as aliases.
- MADR project, https://adr.github.io/madr/ . Template with optional YAML front matter carrying `status` and `date`; the scanner reads `status`, `supersedes` and `superseded-by` from front matter.
- adr-tools by Nat Pryce, https://github.com/npryce/adr-tools . Shell tooling that numbers files `NNNN-title.md` and marks old records superseded; its numbering convention is the one the scanner expects (3 to 5 digits).

The thresholds in this skill (15-word minimum for consequences, the two-engineer-week trigger, the downside word list) are our own working values and are not taken from these sources.
