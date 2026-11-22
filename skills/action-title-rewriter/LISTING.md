# action-title-rewriter

## One line

Turns generic slide titles like "Q3 Results" into short claim titles that the slide body supports, and flags slides whose body states no single claim.

## What it does

The skill takes the text of a slide deck, one title and a few body lines per slide, and works through each slide in a fixed order. It first extracts a single claim from the body lines only, ignoring the old title. It then drafts a title of 15 words or fewer that contains a verb and repeats any number exactly as the cited body lines write it. A title that adds a figure the body does not contain is never produced. Each slide gets one of three support statuses: SUPPORTED when a new title was written, KEPT when the old title already states a matching claim, and UNSUPPORTED when the body gives no claim that can be written within the rules. Unsupported slides keep their old title and are listed under a separate heading with a reason.

The output is a fixed table with six columns, a flagged-slides list, and one counts line. Nothing else is added to the reply, which makes the result easy to paste into a review sheet or check row by row.

## When to use

- A deck where titles are topic labels such as "Churn", "Hiring", or "Roadmap" and the presenter wants the takeaway in each title.
- A review pass where someone needs to see which slides have a body that actually supports a claim.
- Decks of up to 60 slides per request, with short bodies of up to 12 lines per slide.

## When not to use

- Layout, colour, or animation work, or writing speaker notes. The skill only touches titles.
- Adding facts, sources, or statistics to slides. Empty or thin bodies are flagged, not filled.
- Titles that already state a claim the body supports. Those rows are kept as they are.

## Requirements

No script, no installed package, and no network access. Any text-capable agent that can follow a numbered procedure and write a Markdown table can run the workflow. The deck must be supplied as plain text in the request.

## Example

Smoke run on a four-slide input. The table below is the real output of the run described in VERIFICATION.md.

| Slide | Old title | New title | Support status | Body lines used | Note |
|---|---|---|---|---|---|
| 1 | Q3 Results | Q3 revenue reached $4.2M, up 18% from Q2 | SUPPORTED | B1, B2 |  |
| 2 | Churn | Monthly churn fell to 2.1%, while enterprise churn held flat at 0.8% | SUPPORTED | B1, B2 |  |
| 3 | Hiring | We hired 12 engineers in July | SUPPORTED | B1 |  |
| 4 | Roadmap | Roadmap | UNSUPPORTED | - | NO_CLAIM |

## Limits

- The word and verb checks are applied by the agent by reading the text, not by a counter, so a borderline title may need one more pass.
- The banned-word list and the 60-slide cap are working values chosen for this pilot, not editorial standards.
- Hyphenated words count as one word, which can make a title look shorter than a word processor would count it.
- A body written in a language other than the title's language is not checked for meaning, only for the presence of a finite verb and matching numbers.
- The skill does not judge whether a claim is true, only whether the slide body contains it.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
