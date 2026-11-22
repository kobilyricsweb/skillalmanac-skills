---
name: academic-paper-workflow
description: Structures an academic paper (IMRaD or humanities argument), builds a claims-to-sources map and checks a Markdown manuscript against the user's BibTeX or CSL-JSON file with a script, reporting unresolved citation keys, uncited sources, duplicate keys, missing fields and numbers with no citation. Never invents a reference. Use when a student or researcher says outline my paper, IMRaD, add citations, check my references, bibliography errors, citation keys, or claims without sources. Do not use for finding new references, plagiarism or AI-detector evasion, ghostwriting work that must be the student's own, citation style formatting, or LaTeX layout.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, do the manual check in step 5.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
  license: Apache-2.0
---

# Academic paper workflow

Help a writer structure a paper and keep every citation tied to a real source the writer supplied. You organise and check; you do not supply sources.

## The one rule: no invented citations

- A citation key may appear in the manuscript only if it exists in the user's source file (`.bib` or CSL-JSON). Never type a key that is not there.
- Never add, complete or "correct" a source entry from memory: no authors, years, titles, journals, DOIs, page numbers, quotations. A bibliographic detail is valid only if the user typed it or it is in a file the user gave you.
- You may say what a source is *about* only as far as the user's notes, abstract or text say. Specific figures, page numbers and quotations need the user's own material in front of you.
- When a claim has no source, write `[NEEDS SOURCE: <the claim>]` in the text, list it in the report, and tell the user what kind of source would settle it. Do not name a likely paper or author.
- If the user asks you to "add a few references" or "fill in the missing fields", say you cannot do it without inventing, and ask them to supply the sources or details. Offer what you can do: say what the gap is, and suggest search terms and databases for the user to run.

## Workflow

```
- [ ] 1 Collect inputs
- [ ] 2 Choose the structure
- [ ] 3 Build the claim map
- [ ] 4 Draft or edit with keys
- [ ] 5 Run the check and fix
- [ ] 6 Report
```

1. **Collect inputs.** Ask for: the manuscript or outline (as a file if it is long), the source file, and the user's notes on what each source says. Without a source file, build the paper with `[NEEDS SOURCE]` markers and ask the user to supply sources; you may create a skeleton `.bib` only from details the user typed in this conversation.
2. **Choose the structure.** Empirical or STEM papers: IMRaD. Humanities and argument-led essays: question, thesis, sections by theme or chronology, counter-argument, conclusion. If unsure, ask the discipline. Section templates and what each section may cite are in [references/structures.md](references/structures.md); read only the part that matches.
3. **Build the claim map.** For each substantive claim, one row: claim, section, source key, what the source supports (from the user's notes), status (`supported`, `own data`, `NEEDS SOURCE`). Use the table in [assets/claim_map.md](assets/claim_map.md). Claims about the author's own data need no citation but must sit in Methods or Results.
4. **Draft or edit** using Pandoc keys: `[@key]`, `[@a; @b, p. 12]`, narrative `@key`. If the manuscript already uses `\cite{key}`, keep that style. Put each citation inside the sentence it supports, not one sentence later. Keep the author's claims at the strength the source supports ("suggests" does not become "proves").
5. **Run the check, fix, run again:**

```bash
python scripts/manuscript_check.py paper.md refs.bib
```

   Use `refs.json` for CSL-JSON. Read the JSON; it lists every problem with line numbers. Fix by category:
   - `unresolved_keys`: a typo or case difference (see `hint`) can be fixed if the intended entry is obvious; otherwise mark `[NEEDS SOURCE]` and ask the user. Never create the entry.
   - `uncited_sources`: ask whether to cite it (and where, from the user's notes) or leave it out of the bibliography. Do not delete entries yourself.
   - `duplicate_keys`: show both entries; the user decides which to keep. Keys differing only in case count as duplicates.
   - `missing_fields` and `suspect_fields`: list what the user must supply. Do not fill in.
   - `uncited_numeric_claims`: add the right key if the claim map names one; otherwise `[NEEDS SOURCE]`, move it to Methods or Results if it is the author's own data, or soften or cut it.
   - `numeric_claims_covered_by_neighbour`: informational. A citation in the next sentence covers the number; check by eye that it really is the same claim.

   Run the script; do not edit it to make a check pass. Without Python, do it by hand: list every key in the text, look each up in the source file, list entries never cited, and scan the text for digits with no citation near them.
6. **Report** in this fixed shape:

```
Structure: <IMRaD | humanities | other, and what changed>
Citations: <n keys used, n unresolved, n sources uncited, n duplicates>
Source records: <entries with missing or suspect fields, listed for the user>
Claims: <n supported, n own data, n NEEDS SOURCE, with each NEEDS SOURCE claim>
Script: <ok true, or the problems still open>
Not checked: <that sources say what the text says; that sources exist; style rules>
```

## Output contract of `scripts/manuscript_check.py`

Run it with the manuscript first and the source file second. It prints one JSON object (UTF-8) to stdout, also on errors.

```
{
  "tool": "manuscript_check", "version": 1,
  "ok": boolean,                       // true only if every count in "problems" is 0
  "manuscript": string, "sources": string,
  "source_format": "bibtex" | "csl-json",
  "counts": {"entries", "citation_occurrences", "distinct_keys_cited", "numeric_sentences_checked"},
  "problems": {"unresolved_keys", "uncited_sources", "duplicate_keys", "missing_fields",
               "suspect_fields", "uncited_numeric_claims", "parse_errors"},   // integers
  "unresolved_keys": [{"key", "lines": [int], "hint"?}],
  "uncited_sources": [key],
  "duplicate_keys": [{"key", "count", "locations": [int]}],   // line (BibTeX) or item number (CSL-JSON)
  "missing_fields": [{"key", "type", "missing": [string]}],   // "a|b" means one of a, b
  "suspect_fields": [{"key", "field", "value", "reason"}],
  "uncited_numeric_claims": [{"line", "section", "numbers": [string], "sentence"}],
  "numeric_claims_covered_by_neighbour": [same shape],   // informational, not counted in problems
  "parse_errors": [{"line", "key"?, "error"}],
  "skipped_sections": [heading], "notes": [string]
}
Error output: {"tool", "version", "ok": false, "error": string}
```

Exit codes: 0 no findings, 1 findings, 2 input problem (missing, empty or unreadable file; not UTF-8; no entries found).

Options: `--window-after N` (default 1) and `--window-before N` (default 0) set how many neighbouring sentences in the same paragraph may carry the citation; `--all-sections` also scans Methods and Results; `--skip-sections REGEX` replaces the default list of own-data sections. Rules for required fields and for what counts as a number are in [references/checks.md](references/checks.md); read it when a finding looks wrong.

## Boundaries

- This is for writing the user's own paper. If an assignment or journal bans AI assistance, or requires disclosure, say so and follow that rule; do not help hide machine involvement or evade plagiarism or AI-detector tools.
- Do not write whole sections for work the user must author themselves; structure, map, check and give feedback instead.
- Do not paraphrase a source so closely that it is a copy without quotation marks; quote and cite, or summarise in new words and cite.

## Limits

- The script checks form, not truth. It cannot tell whether a source exists or says what the sentence claims; only the user, reading the source, can.
- Numbers are detected by digits. Spelled-out numbers ("three quarters"), claims without numbers, and uncited statements of fact are not found. Single digits and ordinals are ignored; four-digit years count as numbers.
- Citations are recognised in Pandoc (`@key`, `[@key]`) and common LaTeX forms (`\cite{}`, `\citep{}`, `\textcite{}`). A handle such as `@username` is read as a key. Other citation formats (numbered `[1]`, author-year text) are not read.
- Required-field rules follow classic BibTeX entry types and a small CSL-JSON table; styles that need more (a DOI, a publisher place) are not enforced.
- Sentence splitting is heuristic; unusual abbreviations can split or merge sentences.
- BibTeX string macros (`@string`) are not expanded; `@comment` and `@preamble` are skipped.
