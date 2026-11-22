# headline-variant-scorecard

## One line

Ten headline candidates for one article summary, scored 0 to 2 on five criteria with a hard accuracy gate, and the top two picked.

## What it does

The skill takes a plain-text article summary of 80 to 400 words and writes ten headlines: two each from five formulas (number, how-to, question, contrast, specific benefit). It extracts five to eight facts from the summary first, so every headline can be checked against a fixed list. It counts characters and words for each headline, then scores each one on specificity, promise, clarity, accuracy, and length. Length is computed from the counts with a table, not judged by eye. Accuracy is a gate: a headline with any claim missing from the summary cannot be picked, whatever its total. The output is a table of ten rows, a rejected list with the reason for each failed row, and two picks with a one-sentence reason each.

## When to use

Use it when a writer already has an article summary and is choosing among headline options, and wants the comparison written down with the same criteria each time. It suits a draft that has a clear set of facts, such as counts, places, or outcomes, because specificity and accuracy depend on them. It also suits a writer who tends to keep the first headline and wants a checked alternative.

## When not to use

Do not use it to write the article body, to research keywords or search demand, to produce social post copy, or to write headlines for an article whose text was not supplied. It will not add facts that the summary lacks, and it will not pick a headline that promises a result the summary does not give.

## Requirements

A text-capable agent. No network access, no scripts, no extra files beyond the skill folder. The summary must be pasted into the request as plain text.

## Example

Excerpt from a smoke run on a 152-word summary of a library tool-lending pilot. The full run output is in VERIFICATION.md.

| # | Formula | Headline | Chars | Words | Spec | Promise | Clarity | Accuracy | Length | Total | Eligible |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Number | 2,310 Checkouts in Six Months: Harbor Town's Tool Library Pilot | 63 | 10 | 2 | 2 | 2 | 2 | 2 | 10 | yes |
| 2 | How-to | How Harbor Town Built a Tool Lending Pilot in Six Months | 56 | 11 | 2 | 1 | 2 | 1 | 2 | 8 | no |
| 3 | Question | Can a Library Lend Drills Instead of Books? | 43 | 8 | 2 | 2 | 2 | 2 | 1 | 9 | yes |
| 4 | Contrast | Drills, Not Just Books: Harbor Town's Two-Branch Pilot | 54 | 8 | 2 | 2 | 2 | 1 | 2 | 9 | no |
| 5 | Specific benefit | Free 14-Day Tool Loans Reached 38 Percent Repeat Use | 52 | 9 | 2 | 2 | 2 | 2 | 2 | 10 | yes |
| 6 | Number | One in Five Tool Borrowers Had Never Held a Library Card | 56 | 11 | 2 | 2 | 2 | 2 | 2 | 10 | yes |
| 7 | Specific benefit | Free Tool Loans of Up to 14 Days Drew 2,310 Checkouts | 53 | 11 | 2 | 2 | 2 | 2 | 2 | 10 | yes |
| 8 | Contrast | Harbor Town Saves Money by Lending Tools Instead of Buying Them | 63 | 11 | 2 | 0 | 2 | 0 | 2 | 6 | no |
| 9 | How-to | How to Keep a Tool Library Running After a Pilot Ends | 53 | 11 | 1 | 0 | 2 | 0 | 2 | 5 | no |
| 10 | Question | Will the Tool Library Survive Its First Budget Test? | 52 | 9 | 1 | 2 | 2 | 1 | 2 | 8 | no |

Pick: #5 (52 characters) and #7 (53 characters). Both total 10 with every criterion at 2. Headlines #6 (56 characters) and #1 (63 characters) also total 10, so the fewer-characters tie-break puts them third and fourth.

## Limits

The score bands are working values chosen for this procedure, so they are not a standard and two editors may draw the line at different places. Character counts are for plain text and do not account for how a headline renders in a search result or a social card. The accuracy check only compares headlines to the summary it was given. If the summary is incomplete or wrong, the picks will be too. The procedure has no test against a baseline, so it does not show that the picked headlines perform better than the first one a writer would have chosen.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
