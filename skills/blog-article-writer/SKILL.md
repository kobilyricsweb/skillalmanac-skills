---
name: blog-article-writer
description: Writes a new blog article from a signed-off brief (audience, promise, angle, sourced claim table), with numeric structure rules, originality rules and a script that audits the Markdown for heading structure, section lengths, stock openers, uncited numbers, sentence rhythm and internal links. Use when the user says write a blog post, draft an article, write a post that ranks, or turn this outline into an article. Do not use for editing or humanizing an existing text, translation, social posts, ad copy, product documentation or academic papers.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the checklists in steps 4 and 7 by hand.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Blog article writer

This skill authors a new article. It does not edit one: for tightening or de-slopping text that already exists, use a prose-editing skill instead. Here the risks are different: an invented statistic, a generic opener, a section that holds no example.

## Rules that override everything

- No number, date, quotation or "study shows" claim goes in unless it has a row in the brief's claim table with a source URL you have read. If no source exists, cut the claim or rewrite it as an opinion marked as the author's.
- Never invent anecdotes, client stories, first-person experience, quotes or sources. When the piece needs experience the user has not supplied, ask for it in step 1, or use a clearly hypothetical example introduced with "suppose" or "say".
- Do not claim the article will rank. Write what the evidence supports.

## Workflow

```
- [ ] 1 Brief written and checked
- [ ] 2 Intent and shape chosen
- [ ] 3 Information gain found
- [ ] 4 Outline with one idea per H2
- [ ] 5 Draft
- [ ] 6 Audit script run, findings fixed, re-run
- [ ] 7 Final pass and report
```

### 1. Brief contract

Save `brief.md` next to the article. Single-line fields, then a table:

```
Audience: <who, what they already know, 5+ words>
Promise: <one sentence, 8-35 words: what the reader can do or know after reading>
Angle: <the position or method that makes this piece different, 8+ words>
Not covered: <what this article will not do, 3+ words>

| Claim | Source URL | Quote or figure | Checked |
|---|---|---|---|
| <fact, 3+ words> | <URL of the page that holds it> | <the figure or sentence as the source states it> | <YYYY-MM-DD> |
```

The table needs at least 3 rows, each with a page URL (not a homepage). If the user gave a topic only, fill the fields yourself from the request, leave no placeholder, and gather sources with whatever search tools exist; read the page before it enters the table. With no search tool, write the article with no figures and say so in the report. Run `python scripts/article_audit.py brief brief.md` and fix every error before writing. Ask the user only what you cannot decide: the audience when it is truly ambiguous, and any first-hand experience the angle depends on.

### 2. Intent and shape

Choose by what the reader is trying to do. Read [references/shapes.md](references/shapes.md) for the H2 skeleton of the chosen shape; read only that shape.

| Reader intent | Shape | H2 count | Words |
|---|---|---|---|
| Do a task | how-to | 4-8 steps or phases | 900-1,800 |
| Choose between options | comparison | 4-6 | 1,200-2,200 |
| Understand a thing | explainer | 4-7 | 1,000-2,000 |
| Decide whether to believe an idea | argument | 3-5 | 800-1,500 |
| Find a list of things | list | 5-10 items, each an H2 | 1,000-2,500 |

### 3. Information gain

List the 3 points every competing article on the topic makes (read the top results if a search tool exists; otherwise use the user's material). The article must contain at least one element none of them has, chosen from: the user's own data or experience, a worked example with real numbers from a cited source, a decision rule with a threshold, a named common mistake with its fix, a comparison nobody tabulated. Write it into the Angle line. If you cannot find one, say so in the report instead of padding.

### 4. Outline and structure rules

| Part | Rule |
|---|---|
| Title (H1) | Exactly one, at most 70 characters, names the promise. |
| Intro | At most 120 words, before the first H2. Sentence 1 states the situation or the claim with a specific noun or number. By sentence 3 the promise is stated. No history of the topic. |
| H2 | 3 to 10. One idea each: no "and", "&" or ";" in the heading. Name the idea; never "Introduction", "Overview", "Conclusion". |
| H3 | Only under an H2, never skipping a level. |
| Section length | 80 to 450 words. Under 80 it is a label; over 450 it holds two ideas. |
| Example | At least one concrete example per H2: a worked case, code, table, quote, figure. "For example" plus a vague noun does not count. |
| Numbers | Each carries a link or footnote in the same or next sentence, matching a claim-table row. |
| Sentences | Mean 22 words or fewer; no more than 10% over 30 words; mix short and long (spread of 5 words or more). |
| Internal links | One per 500 words, minimum 2, to pages the user supplied. Never invent URLs. |
| Ending | Last section says what to do next or what is still unresolved. No recap paragraph, no "In conclusion". |

### 5. Draft

Write section by section. Each section opens with its claim, then the example, then the consequence for the reader. Read [references/openers.md](references/openers.md) once before writing the intro. Short version: the first sentence must contain a specific number, a named thing, a scene or a claim someone could dispute. Banned in openers and flagged elsewhere: "In today's fast-paced world", "Have you ever wondered", "When it comes to", "In this article we will", "Let's dive in", "in the realm of", "game-changer", "ultimate guide".

### 6. Audit

```bash
python scripts/article_audit.py audit article.md --site-host example.com --brief brief.md
```

Run it; do not edit it to make a check pass. Fix every `error`. Fix each `warning` or write one line in the report saying why it stands (a long section that really is one idea). Re-run until `verdict` is `pass`, or `review` with every warning explained. Exit code 1 means `fix`; exit 2 means the file could not be read.

### 7. Final pass and report

Check by hand what the script cannot see:

```
- [ ] Every H2 opens with its claim; the first and last sentence of each section: removable? If yes, remove
- [ ] Each example is specific enough that a competitor could not have written it unchanged
- [ ] Every figure matches its claim-table cell exactly (units, year, population)
- [ ] The promise in the intro is delivered by the end
- [ ] No sentence states a certainty the source states as a possibility
- [ ] Nothing came from outside the brief, the user's material or a hypothetical marked as one
```

Give the article, then this report:

```
Shape: <shape, words, H2 count>
Audit: <verdict, errors, warnings and what you did about each>
Sources: <rows in the claim table; claims cut for lacking a source>
Information gain: <the one element competitors lack, or "none found">
Not checked: <e.g. source accuracy beyond the cited quote, ranking, facts the user supplied>
```

## Script

`scripts/article_audit.py`: run it; read it only to understand a finding. `audit` prints one JSON object: `words`, `intro_words`, `h2_count`, per-section `words` and `example_signals`, `reading` (mean, median, p90, stdev, shares, grade proxy), `links`, `findings` (each with `severity`, `rule`, `line`, `message`, `match`), `counts`, `verdict` (`pass`, `review`, `fix`). `brief` prints field word counts, claim rows, findings and verdict. Exit 0, 1 or 2 as above; no network; writes nothing. Without Python, do steps 1, 4 and 7 by hand against the tables above.

## Limits

- The audit measures surface features. An "example signal" means a phrase, table, code block, quote or figure is present, not that the example is good. A section can pass and still be dull.
- Uncited-number detection recognises percentages, currency, magnitudes, comma numbers and numbers with common units. Bare counts ("12 plugins") and claims without numbers ("experts agree") are not caught; the final pass must.
- Thresholds are working values for 800 to 2,500 word English articles, not measured optima. The reading-grade proxy uses a syllable heuristic and is a rough guide.
- Nothing here checks that a source says what the table claims; that needs a human or a read of the page.
- Passing the audit does not predict search ranking or reader response.
- English and Markdown only; HTML, CMS exports and front matter other than `title:` are ignored.
- Briefs are read from single-line fields; a value wrapped over two lines is treated as missing.
