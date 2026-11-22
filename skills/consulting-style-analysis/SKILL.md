---
name: consulting-style-analysis
description: Produces a consulting-grade analysis of a business question - an issue tree with a MECE check, hypotheses stated before research, an evidence table with source and confidence, an answer-first pyramid write-up with a so-what line per section and an executive summary of 150 words or less - and validates the tree and evidence file with a script. Use when someone asks for a structured analysis, issue tree, hypothesis-driven approach, MECE breakdown, pyramid principle memo or "why did X happen / should we do X" analysed like a consultant. Do not use for picking between options by debate, stress-testing a plan, mapping claims in a document, open web research, or data crunching.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only, no network. Without Python, follow the manual checks in step 6.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Consulting-style analysis

Turn one business question into a reasoned answer that a reader can check. The order is fixed: question, answer-hypothesis, tree, tests, evidence, write-up. Never gather facts first and look for an answer afterwards.

## Procedure

```
- [ ] 1 Frame the question
- [ ] 2 Write the first answer (governing hypothesis)
- [ ] 3 Build the issue tree with tags
- [ ] 4 Hypothesis per leaf, with a falsifier
- [ ] 5 Collect evidence into rows
- [ ] 6 Validate (script or manual)
- [ ] 7 Write the pyramid
- [ ] 8 Report
```

1. **Frame.** One sentence: decision or question, owner, deadline, and the metric that would settle it. If any is missing, ask once; if the user cannot say, state your assumption in the output. A question like "how is the business doing" is not framed; narrow it ("why did gross margin fall 3 points in Q3, and what should we do").
2. **First answer.** Write a one-sentence answer now, before research. It will probably be wrong in places; its job is to tell you what to test. Store it as `answer`. Revise it at the end, and say if it changed.
3. **Issue tree.** Split the question into branches that are mutually exclusive and collectively exhaustive. Make MECE checkable: on each node with children, list `universe` (the tags for everything the node contains) and give each child `covers` (the tags it owns). A tag in two children is an overlap; a tag in none is a gap. Rules, details in [references/method.md](references/method.md):
   - One splitting rule per level (by formula, by process step, by segment, by time). Mixed rules at one level create overlap.
   - 2 to 5 children per node (hard warning above 7), depth up to 4, leaves small enough to test with one piece of evidence.
   - Add an explicit "other" child only with a stated size limit; otherwise the split is not exhaustive.
   - Name branches with what they are, not verbs ("Price", not "Fix price").
4. **Hypotheses.** For every leaf write one falsifiable statement and a `falsifier`: the specific result that would make it wrong. "Churn is higher in the first 30 days" is testable; "customer experience matters" is not. Prune leaves you cannot attach a test to.
5. **Evidence.** One row per fact: `claim`, `source` (document, page or table, date, or who said it), `source_type`, `direction` (supports or refutes the hypothesis), `confidence` from 0 to 1. Confidence rubric and ceilings per source type are in method.md; the script warns when a row exceeds its ceiling. Record refuting evidence as carefully as supporting evidence. A hypothesis with no refuting search is untested, not confirmed. Never invent a source; if there is none, the row is `assumption` with confidence 0.4 or less.
6. **Validate.** Save everything as one JSON file (get the skeleton with `python scripts/analysis_check.py template`), then run:

```bash
python scripts/analysis_check.py check analysis.json
```

   Run the script; do not edit it to make a check pass. Fix every `errors` entry and re-run until `"ok": true`; read each warning and either fix it or give the reason in the report. Without Python, check by hand: every tag appears in exactly one sibling; every hypothesis has at least one evidence row and a falsifier; every row has a source and a confidence between 0 and 1; the summary is 150 words or less (count them); every section ends with a so-what.
7. **Pyramid write-up.** Order of the document:
   1. Executive summary, 150 words at most: the answer in the first sentence, the 2 to 4 reasons, the recommended action and its owner or date. No method description, no history.
   2. One section per supporting argument. Section title is a full-sentence claim ("Margin fell because freight rates rose 18%"), not a topic ("Freight"). First sentence repeats the claim; evidence follows; the last line is `So what:` with the implication or action for the reader, not a recap.
   3. Arguments at one level are the same kind (all reasons, or all steps) and ordered by importance, time or structure, said explicitly.
   4. Appendix: the issue tree and the evidence table.
   Section titles read in sequence must tell the whole story. If the answer changed from step 2, say what changed and why.
8. **Report** in this fixed shape after the document:

```
Answer: <one sentence>
Tree: <nodes, leaves, MECE check passed or the warnings kept and why>
Evidence: <rows, share at confidence >= 0.7, rows that are assumptions>
Changed from first answer: <yes/no and what>
Not checked: <what you could not source; what the script cannot see>
```

## Script

`scripts/analysis_check.py`: run it. `check` prints strict JSON: `ok`, `error_count`, `warning_count`, `counts` (nodes, leaves, hypotheses, evidence, sections, summary_words), `errors` and `warnings` as lists of `{code, where, message}`. Exit 0 when no errors, 1 with errors, 2 on an unreadable file or invalid JSON (plain message on stderr). `template` prints a valid skeleton input. Error codes include `tree-overlap`, `tree-gap`, `tree-universe-missing`, `tree-covers-missing`, `hypothesis-no-evidence`, `hypothesis-no-falsifier`, `evidence-no-source`, `evidence-confidence-range`, `summary-too-long`, `section-no-so-what`.

## Boundaries

- This skill structures reasoning; it does not create facts. Figures must come from the user's files, sources the user names, or search you actually performed. Mark anything else as an assumption.
- A passing validation shows the structure is sound, not that the conclusion is right. Never say "validated" about the conclusion.
- Not for decisions about people (hiring, firing, grading individuals) presented as objective analysis.

## Limits

- MECE is checked only through the tags you declare; the script cannot tell whether the tags are the right ones.
- The confidence numbers are judgement scores on a rubric, not probabilities; ceilings per source type are working values.
- Word counting splits on spaces, so hyphenated words and numbers count as one word each.
- English-language checks only for the so-what length rule; other languages work for structure.
- The script does not read documents, check sources exist, or verify numbers.
