# social-flyer-design-brief

## One line

Turns a request for a social post, flyer or slide into a written brief with a copy deck, character budgets and two layout options, before anyone opens a design tool.

## What it does

The skill walks through seven fixed steps. It collects the intake fields (goal, audience, format, size, key message, mandatory text, and any brand or image material), then states one primary message and checks that the text levels stay within three. Each text block gets a character budget that depends on the format, so a headline for a flyer is capped at 40 characters and a headline for a square social post at 30. Drafts are counted against those budgets and marked as fitting, trimmed or open.

The brief then describes two layout options in words, each with a reading order, an anchor position, an image zone, a detail block placement and a minimum empty area. A contrast line is added for any colours the user supplied, using the published WCAG ratios. The last parts are an export checklist with file-name pattern and a short list of open questions.

Nothing is drawn, and no colours, logos or fonts are chosen for the user. Mandatory details such as dates and contact points are copied exactly as given and never retyped from memory.

## When to use

Use it when a person has a graphic to make from a blank canvas and wants the wording, hierarchy and sizes settled first. Typical cases are a bake-sale flyer, a club event post, a conference slide title or a shop announcement. It is most useful when the person has the facts but not the copy.

## When not to use

Do not use it to produce the artwork, to suggest imagery, or to invent a brand identity. It does not say whether a particular design tool has a feature, because the procedure is tool-neutral. It is also not a legal or marketing-claims review: claims about results need a source from the user.

## Requirements

A text-capable agent. No tools, network access or Python are needed.

## Example

Excerpt from the offline smoke run (bake-sale flyer), copied from VERIFICATION.md:

    ## Copy deck
    | Block | Level | Budget | Draft | Count | Status |
    |---|---|---|---|---|---|
    | Headline | L1 | 40 | Bake sale for the school library | 32 | fits |
    | Support line | L2 | 70 | Every cake and cookie you buy pays for new books for our readers. | 65 | fits |
    | Detail | L3 | 90 | Saturday 13 June, 09:00 to 13:00, school main hall. | 51 | fits |
    | Call to action | L3 | 30 | Come along and buy a cake. | 26 | fits |
    | Handle or link | L3 | 40 | [to supply] | 11 | open |

## Limits

The budgets and size tables are working values chosen for this procedure, not industry standards. Only the contrast ratios come from the WCAG 2.x specification. The skill cannot judge whether the copy is persuasive, accurate for the event, or suited to the audience, and it does not check the finished artwork. The layouts are described, not drawn, so they will need a designer or a person to turn them into a file. Input that has no key message or no mandatory text is refused until those are supplied.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
