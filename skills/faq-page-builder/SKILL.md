---
name: faq-page-builder
description: Builds an FAQ page from supplied customer questions and facts. Merges duplicate questions, groups them into four to six intents, writes answers of at most 60 words from the supplied facts only, marks unanswered questions TO-CONFIRM, and emits a FAQPage JSON-LD block matching the page text. Use when a team holds real support questions with frequency counts and wants a structured FAQ page. Do not use for inventing policies or prices, marketing copy, answers about one customer's account, or schema for non-FAQ pages.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B); no network access and no scripts are needed.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# FAQ Page Builder

Turns a pasted list of customer questions, each with a frequency count, plus a list of supplied facts into one FAQ page: grouped, ordered, answered only from the facts, with a JSON-LD block that matches the visible text.

## Intake

Each question line is `<count> | <question>`. The count is a positive whole number of times the question was asked. Each fact line is `F<n> | <fact sentence>`. If fact lines have no IDs, number them F1, F2, and so on in input order.

## Workflow

1. **Check intake.** Required: R1 every question line has a positive integer count; R2 at least one fact line exists; R3 at most 60 question lines. If any check fails, stop and return the BLOCKED output in the contract below. Output: the R1 to R3 result for each check.
2. **Normalize.** Lowercase the text, delete the characters `. ? ! , ; :`, collapse spaces, and drop stopwords: a, an, the, i, my, your, do, does, can, how, what, when, is, to, of, me, you, it, be. No stemming, so "ship" and "shipping" are different words. Output: the normalized form of each line.
3. **Merge duplicates.** Two lines merge when their normalized texts are identical, or when the Jaccard similarity of their remaining words is 0.6 or higher. Merge by summing counts. The page wording is the most frequent source wording; on a tie, take the earliest line. Output: one merged question per row, with its source line numbers and total count.
4. **Group by intent.** Assign every merged question to one group. Use 4 to 6 groups. Name each group in 2 to 4 words, sentence case. Output: group name and member merged questions.
5. **Order.** Sort groups by total count, highest first; on a tie, sort by group name A to Z. Sort questions inside a group by total count, highest first; on a tie, keep input order. Output: the ordered list.
6. **Write answers.** Use only the facts that support the question. Each answer is 1 to 60 words, counted as whitespace-separated tokens, and cites its fact IDs in section 5. Use "Yes" or "No" only when a fact states the answer directly. Output: one answer per merged question.
7. **Mark TO-CONFIRM.** If no fact answers a question, or two facts conflict on it, the question is TO-CONFIRM. Record the fact that is missing. Output: TO-CONFIRM rows.
8. **Build JSON-LD.** Include only answered questions, in page order. For each one, `name` is the page question and `text` is the page answer, character for character. Use straight ASCII quotes and no HTML. Check that the block parses as JSON before you return it. Output: one FAQPage block.
9. **Assemble and set status.** Write the five sections in the order below. Set the status from the TO-CONFIRM count.

## Thresholds and decision table

| Rule | Value | Action when violated |
|---|---|---|
| Question lines per run | 1 to 60 | Above 60: BLOCKED, ask the user to split the list into batches of 60 or fewer |
| Duplicate merge (Jaccard, working value) | 0.6 or higher, or identical after normalization | Merge and sum counts |
| Groups | 4 to 6 (target), 6 maximum | Above 6: merge the two smallest groups until 6 remain. Below 4 only when the input has fewer than 4 distinct intents |
| Answer length | 1 to 60 words | Shorten. If it cannot fit without dropping a fact, make it TO-CONFIRM |
| Digits in an answer | Each digit token must appear in a cited fact | Rewrite. If that is impossible, make it TO-CONFIRM |
| TO-CONFIRM | A question no fact answers, or whose facts conflict | Listed in section 4 and left off the page and the JSON-LD block |
| Status COMPLETE | 0 TO-CONFIRM questions | Output the full page |
| Status PARTIAL | 1 or more TO-CONFIRM questions | Output the full page with the TO-CONFIRM list |
| Status BLOCKED | Any intake check R1 to R3 fails | Output only the status table and the question list |

## Intake checks

| Check | Fails when | Item in the BLOCKED list |
|---|---|---|
| R1 | A question line has no count, a zero count, or a decimal count | "Line N has no positive whole count." |
| R2 | No fact line is present | "Add at least one fact line in the form F1 \| fact sentence." |
| R3 | More than 60 question lines are present | "Split the list. Each run takes 60 lines or fewer." |

## Answer rules

1. Open the answer with the direct response to the question. Use "Yes" or "No" only under the step 6 rule.
2. Copy numbers, units, and ranges from the fact as written, for example "5 to 7 business days". Do not convert units or round.
3. Keep the spelling used in the fact. Use US English in every new sentence.
4. Write one paragraph of complete sentences. No bullet lists, line breaks, HTML, or links.
5. Add no reassurance and no sales language, such as "We value your business."
6. Repeat a fact in several answers when several questions need it. Never write "see above" or refer to another answer.
7. The page question is the most frequent wording. If it has no question mark, add one.

## Output contract

The output has five sections. Each is an H2 heading titled exactly `1. Status`, `2. Page`, `3. JSON-LD`, `4. TO-CONFIRM`, or `5. Merge and fact log`, in that order. No other H2 headings are used.

**1. Status** is a two-column table with the rows Status, Raw questions, Merged questions, Groups, Answered, TO-CONFIRM, and Total count. Status is one of COMPLETE, PARTIAL, or BLOCKED. Total count is the sum of every input count.

**2. Page** has one `### <Group name>` heading per group, in order. A group with no answered question is left out. Under each heading, each answered question is a `#### <question>` heading followed by its answer as one paragraph.

**3. JSON-LD** is one fenced `json` block: an object with `@context` set to the schema.org vocabulary address, `@type` set to FAQPage, and `mainEntity` as an array of Question objects. Each Question has `@type`, `name`, and `acceptedAnswer` with `@type` set to Answer and `text`.

**4. TO-CONFIRM** is a table with the columns #, Question, Count, Missing fact. It is empty when Status is COMPLETE; then write the single line "None".

**5. Merge and fact log** has two tables. The first is Merged question, Source lines, Total count, Facts cited. The second is Fact ID, Fact text, listing every fact cited in any answer.

**BLOCKED output** replaces sections 2 to 5 with a numbered list of at most 10 items. Each item names one missing or invalid intake item, for example "Line 4 has no count. Give the count for: <question>".

## Refuse or stop when

1. Any intake check R1, R2, or R3 fails. Stop with BLOCKED and the numbered list. Do not guess a count.
2. A number, price, time, percentage, or policy appears in an answer and is not in a cited fact.
3. A question needs a fact that was not supplied. Make it TO-CONFIRM. Never fill the gap from general knowledge.
4. Two facts conflict on the same topic. Make the question TO-CONFIRM with the missing fact "conflict between F<a> and F<b>".
5. A question asks about one customer's order, account, charge, or refund status. Make it TO-CONFIRM with the missing fact "account lookup required", and do not answer it.
6. A question asks for legal, tax, or medical advice. Make it TO-CONFIRM with the missing fact "owner review required".
7. The JSON-LD text differs from the page text by even one character. Rewrite the block from the page text before you return it.

## Files

This skill ships two files: [SKILL.md](SKILL.md), the procedure, and [LICENSE.txt](LICENSE.txt), the Apache-2.0 license text.
