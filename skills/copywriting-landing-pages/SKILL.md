---
name: copywriting-landing-pages
description: Writes and audits landing-page copy in a fixed five-section contract (hero promise, proof, how it works, objections, CTA) with one message per section, a source for every number, length limits per block and a banned-phrase list, plus a script that checks a Markdown or HTML draft and prints strict JSON. Use when the user asks for landing page copy, a hero headline, a homepage or signup page rewrite, wants hype or unsourced stats removed, or says the page does not convert. Do not use for campaign plans or briefs, ad or email copy, SEO keyword work, or full site design.
license: Apache-2.0
compatibility: The audit script needs Python 3.9 or newer, standard library only, and makes no network calls. Without Python, apply the checklists in steps 3 and 6 by hand.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Copywriting landing pages

A landing page has one job: get one kind of visitor to take one action. The copy states a promise, proves it, shows how, answers the reasons not to act, and asks once. Everything else is cut.

## Inputs to collect first

Do not write until you have these five. If one is missing, ask for it or write it as `[NEEDED: ...]` and say so in the report. Never invent them.

| Input | Why it blocks writing |
|---|---|
| The visitor: who, and the situation they arrive in | The promise is about their problem, not your product |
| The one action and its destination URL | CTA wording and the final section depend on it |
| The outcome in the visitor's terms | The hero promise |
| Proof the user actually holds: numbers with a source, named customers, quotes with attribution, dates | Section 2 is built only from this |
| The real objections: price, effort, risk, switching, "does it work for me" | Section 4 |

## Section contract

Order is fixed. One H1, then H2 sections. Limits are words, counted without link URLs.

| # | Section | Job | Limits | Heading words the script reads |
|---|---|---|---|---|
| 1 | Hero (H1) | One promise to one visitor, one sentence of support, the primary CTA | Headline 3 to 12 words (over 14 is an error). Support 30 words at most (over 45 is an error), CTA excluded | The H1 itself |
| 2 | Proof | Evidence that the promise holds, before the explanation | 150 words | proof, customers, results, testimonials, case study |
| 3 | How it works | 3 to 5 numbered steps from the visitor's first action to the promised outcome | 180 words | how it works, steps, process |
| 4 | Objections | One answer per real objection, each starting with the plain answer (yes, no, a number) | 300 words | questions, FAQ, pricing, guarantee, risk |
| 5 | CTA | The same action as the hero, restated once | 60 words | start, try, book, ready, get started, join |

Rules that apply to every section:

- **One message per section.** A section may support its heading and nothing else. If a paragraph does not serve the heading, move it or cut it. Section headings are 10 words at most; paragraphs and list items 50 words at most; more than 4 sub-headings in a section signals several messages.
- **The headline is a promise, not a label.** Outcome plus the visitor, or outcome plus the time or effort: "Send invoices that get paid on time", not "Welcome to Tallybook". A headline that joins two ideas with "and", "&" or ";" holds two promises: keep one.
- **Order matters.** Proof comes before the explanation because a visitor who doubts the promise will not read the steps.
- A page may drop proof or objections only when the user says so; the audit takes `--optional proof,objections`. State what is missing in the report.

## Claim substantiation rule

Every number in the copy has a source in the same sentence or immediately after it, or the number is removed. No exceptions for round numbers, "industry knowledge" or numbers the user "remembers".

| The text says | Do this |
|---|---|
| A percentage, multiplier (3x), money saved, time saved, count of customers or users, rating, rank (#1, top 10) | Source needed: a link to the page or file, `Source: <name, date>`, a footnote with a definition, or `(Author, year)` |
| "Thousands of", "millions of", "many companies", "trusted by leading brands" | Replace with the exact count and its source, or delete. These are numbers with the number removed |
| A price, plan limit, trial length, refund window | Not a performance claim; it is a term. State it exactly as the billing system does and keep it in step with the pricing page |
| A testimonial with a figure in it | Quote only with a named person and role next to it (an attribution line starting with a dash). No attribution, no quote |
| A superlative ("the best", "number one", "fastest") | Needs a named comparison, a date and a source; otherwise delete |
| The user gives a number with no source | Keep it out of the draft or mark `[NEEDED: source for 61%]`. Say so in the report |

A source must say what was measured, on whom, and when. "Our internal data" is allowed only with the date and sample size. Do not round up, drop a qualifier ("up to", "median") or move a figure from one period to another.

## CTA grammar

- The label is a verb plus an object, 2 to 5 words: "Start the free trial", "Book a 20-minute demo". Not "Submit", "Click here" or "Learn more"; nothing in all caps; no exclamation mark.
- The label says what happens next, not what the visitor feels.
- One primary action per page. Every primary CTA goes to the same destination. At most two wordings of it (for example hero and final), at most 4 primary CTAs on the page and 2 in any one section.
- The hero and the last section each carry one. A secondary link to an in-page anchor is allowed and is not counted.
- Next to the CTA, one line may remove a barrier with a real term ("No card needed. 14-day trial.") and only if the user confirmed it.

## Workflow

Copy this checklist and tick it off:

```
- [ ] 1 Collect the five inputs
- [ ] 2 Draft in Markdown, section by section
- [ ] 3 Self-check against the contract
- [ ] 4 Save to a file and run the audit
- [ ] 5 Fix errors, then warnings, re-run
- [ ] 6 Report
```

1. **Collect** the inputs above. For a rewrite, read the existing page first and list its numbers, claims and CTAs.
2. **Draft** in this order: proof inventory (what is real), objections list, hero, proof, how, objections, CTA. Use the heading words from the table so the page is auditable. Use plain words: short sentences, the reader's vocabulary, active verbs, "you" for the visitor.
3. **Self-check**: each number sourced; each section one message; hero within limits; CTA label grammar; banned phrases from [references/rules.md](references/rules.md) absent; reading level about grade 8 or lower.
4. **Run** the audit on the saved file:

```bash
python scripts/lp_audit.py page.md
python scripts/lp_audit.py page.html --optional proof
```

   Options: `--format auto|markdown|html` (default auto); `--optional` with a comma list of `proof,how,objections,cta` to downgrade a deliberately missing section to a warning; `--strict` to fail on warnings too. Run it; do not edit it to make a check pass.
5. **Fix** every `error`; fix each `warn` or say why it stays. For `unsupported-number` the fix is a source or a deletion, never a softer-sounding number. Re-run until `verdict` is `pass`.
6. **Report** in this fixed shape, after the copy:

```
Page: <one-line promise and the one action>
Audit: <verdict>, <errors> errors, <warnings> warnings (<file>, <date run>)
Sources used: <each number and where it came from>
Removed or marked NEEDED: <numbers and claims left out for lack of a source>
Kept on purpose: <warnings left, with reason>
Not checked: <e.g. truth of sources, legal review of guarantees, rendering, A/B results>
```

## Script contract

`scripts/lp_audit.py <file> [--format ...] [--optional ...] [--strict]` prints one JSON object. Exit 0: no errors. Exit 1: errors (or warnings with `--strict`). Exit 2: usage, unreadable or empty file, with a plain message on stderr. Fields:

```
tool, schema (1), file, format ("markdown"|"html"),
verdict ("pass"|"fix"), counts {error, warn},
stats {hero_headline_words, hero_support_words, words, sentences,
       fk_grade (null under 40 words), avg_sentence_words,
       unsupported_claims, banned_hits, cta_count},
sections [{role: hero|proof|how|objections|cta|other, heading, line, words}],
findings [{check: sections|hero|blocks|claims|banned|cta|reading,
           severity: error|warn, line, rule, text, fix}]
```

Rule ids: `missing-<role>`, `order`, `no-h1`, `multiple-h1`, `headline-long`, `headline-short`, `two-promises`, `support-long`, `hero-no-cta`, `heading-length`, `paragraph-long`, `section-long`, `too-many-subheads`, `unsupported-number`, `vague-quantity`, `banned-phrase`, `no-cta`, `cta-grammar`, `cta-destination-split`, `cta-label-variants`, `cta-count`, `cta-per-section`, `final-no-cta`, `grade-high`, `sentence-long`. Thresholds and the reason for each: [references/rules.md](references/rules.md), which also holds the banned-phrase list and the source patterns.

Markdown convention: `[Text](url "cta")` forces a link to count as a CTA. In HTML, `<button>` and anchors with class `btn`, `button` or `cta` count. Source patterns accepted for a number: an external link in the sentence or as the next sentence, `Source: ...`, `according to`, a `[^n]` marker with a footnote definition, `(Author, 2025)`, `as of <month> <year>`, `n = <count>`, or a quote followed by an attribution line.

If Python is unavailable, do the step 3 self-check by hand and write "audit not run" in the report.

## Boundaries

- Write copy only for claims the user can substantiate. If asked for a figure, testimonial, award or customer logo the user does not have, decline to invent it and offer the placeholder.
- No fake urgency (countdowns, "only 3 left") and no fake social proof. A deadline is allowed only if real and dated in the same sentence.
- Health, finance, legal and earnings promises, and anything "guaranteed", need the user's own legal review; mark them in the report.

## Limits

- The script reads structure and surface patterns. It cannot tell whether a cited source is real, current or says what the copy claims, and it cannot judge whether a promise is persuasive or true.
- Section roles are guessed from heading words; a page with unusual headings shows `other` and gets "missing" errors. Rename headings with the hint words or pass `--optional`.
- Numeric claim detection covers percentages, multipliers, money, counts of people or businesses, time saved, ratings and ranks. A claim written in words ("twice as fast", "one in three") is not detected; check those by eye.
- The reading grade is a Flesch-Kincaid proxy with a rough syllable count, reported only for 40 words or more. It is a smell test, not a readability study.
- Thresholds are working values from common practice, not measured on conversion data. This skill does not predict conversion; only an experiment on the live page does.
- English copy only. The script does not execute or render HTML and ignores scripts, styles and head content.
