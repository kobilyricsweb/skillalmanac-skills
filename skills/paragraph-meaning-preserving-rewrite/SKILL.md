---
name: paragraph-meaning-preserving-rewrite
description: Rewrites a supplied paragraph in new wording while keeping every claim, number, name and date, then reports a claim-by-claim table and before-and-after counts. Use when the user asks to rewrite, reword, paraphrase or restyle a paragraph and the facts must stay the same. Do not use for adding or removing facts, for rewriting to evade plagiarism or AI-detection checks, for translation, or for summarizing several documents.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Paragraph meaning-preserving rewrite

Type B skill. No script ships with it. The agent does the splitting, rewriting and counting itself, then returns the output contract below. Shipped files: [LICENSE.txt](LICENSE.txt).

## Intake

Required: the paragraph, 20 to 300 words of prose.
Optional: tone (neutral, formal, casual, plain or warm; default neutral), and a length target (a word count, or "shorter" or "longer").
If the paragraph is missing or out of range, stop (see the Refuse / stop when list).

## Workflow

1. Check intake. Count the original words by splitting on whitespace; a hyphenated word or a contraction counts as one word, and a number counts as a word. Output: the original word count and the tone and length setting, recorded for the Settings section.
2. Split the paragraph into claims. One claim is one independent assertion. Split at sentence ends, and at "and" or "but" only when both sides are independent clauses. A relative clause ("who", "where", "which") or a "with" phrase that adds a fact is its own claim. Number the claims C1, C2 and so on in source order. Output: the numbered claim list with the original wording of each claim.
3. Extract the counts from the original text using the definitions below. Output: the Original column of the Count check.
4. Rewrite claim by claim, then join the claims in the original order into one paragraph. Keep every number, name and date, the modal verbs (may, might, must, likely, could), the hedges (about, nearly, at least, roughly), and the referent of every pronoun. Change sentence structure, word choice and tone only. Output: the rewritten paragraph.
5. Check the length against the Length table. Output: one row for the Length check.
6. Build the claim table. Each claim gets the rewritten span that carries it and a Kept value of yes or no. Output: the Claim table.
7. Recount numbers, names and dates in the rewrite. If any count differs from step 3, revise the rewrite and recount. Two revisions at most. Output: the Rewritten column of the Count check, with a Match value for each row.
8. Set the status using the Status table, then assemble the sections in the order of the output contract.

## Definitions for counting

| Category | Counts as | Does not count as |
|---|---|---|
| Number | Digit token (12, 2.5, 1,200, 40%), or cardinal word one to twenty, thirty, forty, fifty, sixty, seventy, eighty, ninety, hundred, thousand, million, billion | Ordinals (second, third), seasons, "a" |
| Name | Each occurrence of a proper name for a person, place, organization or work. "Maria Lopez" is one occurrence. | Pronouns, job titles without a name, capitalized common words at the start of a sentence |
| Date | Month name, weekday name, four-digit year, or numeric date such as 3/4/2021 | Seasons (spring, fall), times of day, relative terms (next week, last year) |

Relative terms are not counted, but they are still claims and must be kept in the rewrite.

## Tables with concrete values

Claim count by original word count (working value; a check, not a rule):

| Original words | Expected claims |
|---|---|
| 20 to 49 | 2 to 5 |
| 50 to 89 | 4 to 8 |
| 90 to 149 | 6 to 12 |
| 150 to 300 | 10 to 20 |

If the claim count falls outside the expected range, re-check step 2 before rewriting.

Length target (working value):

| Case | Target band for the rewritten word count |
|---|---|
| No length target from the user | 80 percent to 120 percent of the original count |
| User gives a word count | Within 10 percent of that number |
| User says "shorter" with no number | 60 percent to 90 percent of the original count |
| User says "longer" with no number | 110 percent to 140 percent of the original count |

A result outside its band gets one more revision. If it is still outside the band, status is partial and the gap goes under Open questions. Never add or drop a claim to reach a band.

Request clause handling:

| Clause in the request | Action |
|---|---|
| Asks to add a fact, number, name, date or source | Refuse that clause only. Keep the rest. Status partial. List the refused clause under Open questions. |
| Asks to remove, round or change a number, name or date | Refuse that clause only. Keep the original value. Status partial. List it under Open questions. |
| Asks for a different tone | Apply it. The facts do not change. |
| Asks to rewrite so a plagiarism or AI-detection check does not flag the text | Refuse the whole request. Status refused. No rewrite. |

Status values:

| Status | When it applies |
|---|---|
| complete | Every claim has Kept yes, all three count rows match, the length is in its band, and every request clause was fulfilled. |
| partial | At least one claim has Kept no, a count still differs after two revisions, the length is outside its band, or one request clause was refused. |
| needs-input | No paragraph was supplied, or the paragraph is outside 20 to 300 words. No rewrite is produced. |
| refused | The request asks for evasion of a plagiarism or AI-detection check. No rewrite is produced. |

## Output contract

Use these headings in this order. Omit the sections that a needs-input or refused status does not produce.

Line 1: `Status: <complete | partial | needs-input | refused>`

`## Rewrite`: one plain-text paragraph. No bullets, no headings inside it.

`## Claim table`: columns `Claim | Original claim | Rewritten wording | Kept`. One row per claim, in C1 to Cn order. Kept is `yes` or `no`.

`## Count check`: columns `Category | Original | Rewritten | Match`. Rows are Numbers, Names and Dates, in that order. Match is `yes` when the two counts are equal.

`## Length check`: columns `Original words | Rewritten words | Ratio | Target band | Result`. Ratio is rewritten words divided by original words, to two decimals. Result is `within` or `outside`.

`## Settings`: columns `Setting | Value`. Rows are Tone and Length target. Use `neutral` and `none given` when the user gave no value.

`## Open questions`: a numbered list of refused clauses, unresolved count mismatches, length gaps and missing intake facts. Write `None` when there are none.

For needs-input, the Open questions list is the numbered question list. Ask for the missing paragraph first, then any optional setting the user wants to change.

## Refuse / stop when

- No paragraph is supplied, or it has fewer than 20 or more than 300 words. Return status needs-input and a numbered question list under Open questions. Stop there.
- The text is a table, code block or bulleted list rather than prose. Return needs-input and ask whether the prose parts alone should be rewritten. Stop there.
- The request asks to rewrite so a plagiarism or AI-detection check does not flag the text. Return status refused. Do not rewrite any part of the text.
- A clause asks to add, remove, round or change a fact. Refuse that clause only, as the table above says.
- The source contains two claims that contradict each other. Keep both as written, mark Kept yes for each, and set status partial with the contradiction under Open questions.
- A length floor or band cannot be reached without a dropped claim or an invented fact. Keep every claim, deliver the shorter or longer text, and set status partial.

Never invent a fact to reach a length band, and never reword a number, name or date into a different value.
