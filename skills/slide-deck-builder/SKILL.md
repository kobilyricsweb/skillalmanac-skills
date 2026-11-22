---
name: slide-deck-builder
description: Plans, writes and reviews slide decks, pitch decks and talks, with one message per slide, takeaway headlines, six lines at most, evidence slides, an appendix for detail and speaker notes. Use when the user asks for a presentation, slide deck, pitch deck or board update, or wants slides tightened, reviewed or given notes. A script validates an outline or .pptx for crowded slides, topic headlines, missing notes, duplicate headlines, charts without a source and images without alt text. Do not use for brand templates or theme design, Word or PDF reports, posters, or a single chart with no deck.
license: Apache-2.0
compatibility: The checker script needs Python 3.9 or newer, standard library only. No network access is used and nothing is installed. Without Python, check the rule table in the script section by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Slide deck builder

A deck is a spoken argument with visual support. The audience reads a slide in about five seconds and then listens, so every slide carries one message, and the headlines alone must tell the whole story. Build the outline and notes first, check them with the script, and only then generate a file.

## The deck contract

| Rule | Limit | Why it is a number |
|---|---|---|
| One message per slide | 1 | Two messages means two slides |
| Headline | A full sentence with a verb that states the takeaway, 15 words at most. "Churn fell 6 points after the new flow", not "Churn results" | The headline is what people remember |
| Body | 6 lines and 50 words at most per main slide | Past this the audience reads instead of listens |
| Chart | 1 per slide, with a stated source, and the headline says what to see in it | A chart without a claim is decoration |
| Images | Every image has a description (alt text) | Accessibility and a second check that the image earns its place |
| Speaker notes | 25 to 220 words on every main slide: what to say, the number to remember, the hand-off to the next slide | Notes under 25 words are a label; over 220 get read aloud |
| Appendix | After a slide headed "Appendix", up to 12 lines and 120 words, no notes needed, never required to follow the story | Detail lives here so the main slides stay light |
| Headlines | No two alike | Duplicates signal copy-paste or a missing point |

Read [references/deck-contract.md](references/deck-contract.md) for the deck structures by purpose, the slide count rule, the evidence slide pattern, the speaker notes template and the visual rules (type sizes, contrast, chart rules). Read only the section you need.

## Workflow

Copy this checklist and tick it off:

```
- [ ] 1 Brief
- [ ] 2 One-sentence message
- [ ] 3 Headline spine
- [ ] 4 Evidence and body
- [ ] 5 Speaker notes
- [ ] 6 Validate the outline
- [ ] 7 Generate the file
- [ ] 8 Inspect the file and report
```

1. **Brief.** Settle five things from the request; ask only about what is missing and cannot be guessed: audience and what they already know; the one decision or belief you want from them; the time slot in minutes; delivery (live in a room, video call, or sent to read); hard constraints (template, language, numbers that must appear). If the deck will be read without a speaker, say so: it needs fuller body text and the notes move onto the slides, and this contract's body limits become a trade-off to state in the report.
2. **One-sentence message.** Write the single sentence the audience should repeat tomorrow ("Guest checkout cut abandonment by a third; approve two more markets"). Everything must support it or move to the appendix.
3. **Headline spine.** Write only the headlines, in order. Apply the headline-reading test: read them in sequence with nothing else; if they do not tell the story and end on the ask, rewrite the spine before writing any body. Slide count: speaking time is three quarters of the slot, and one content slide takes 1.5 to 2 minutes of it, plus a title slide. A 20-minute slot is 7 to 10 content slides, not 25.
4. **Evidence and body.** Under each headline put only what proves it: at most 6 short lines, or one chart, or one table. Use the evidence slide pattern in the reference: claim headline, one chart with the point highlighted, a source line. Move raw tables, methods and caveats to appendix slides. Put numbers in with their unit and period, and take them from the user's data; never invent a figure, a source or a client name. A missing number becomes a visible placeholder like `[TBC: Q3 revenue]` and goes in the report.
5. **Speaker notes.** Every main slide gets notes following the template: opening line, the point, the one number to remember, the hand-off sentence. Notes are written to be spoken, in first person, not a copy of the slide.
6. **Validate the outline.** Write the outline in the format of [references/outline-format.md](references/outline-format.md), then run:

   ```bash
   python scripts/deck_check.py outline.md
   ```

   Fix every error and every warning you cannot defend, then run again until `"ok": true`. Warnings that are deliberate (a title slide, a divider) are named in the report. Run the script; do not edit it to make a check pass.
7. **Generate the file.** Pick the generator by the table in [references/generators.md](references/generators.md): python-pptx when the user needs an editable .pptx, Marp when Markdown to PPTX or PDF is enough, reveal.js for a browser talk. Check what is installed first (`python -c "import pptx"`, `marp --version`); if the tool is missing, tell the user the exact install command and wait for approval. Never install packages unasked. If nothing is available, deliver the validated outline as the deliverable and say a generator is needed. Apply the visual rules from the reference when building.
8. **Inspect and report.** For a .pptx run `python scripts/deck_check.py deck.pptx`, fix, rerun; then render to images or PDF if a renderer exists and look at every slide for overflow, overlap and unreadable contrast. Report in this fixed shape:

   ```
   Deck: <file or outline>, <n> slides (<m> main, <k> appendix), planned for <minutes> min
   Message: <the one sentence>
   Check: ok true/false, <errors> errors, <warnings> warnings (deliberate ones listed)
   Placeholders: <numbers or sources still to fill, or none>
   Not checked: <e.g. rendering, fonts on the presenting machine, facts against sources>
   ```

## The script

`scripts/deck_check.py <file>` accepts `.md`, `.json` or `.pptx` and prints one JSON object: `slide_count`, `appendix_starts_at`, per-slide `body_lines`, `body_words`, `notes_words`, `charts`, `images`, a `findings` list (`slide`, `severity`, `rule`, `message`), `counts` and `ok`. Exit 0 means no errors, 1 means errors, 2 means unreadable input. Options: `--max-lines N`, `--max-words N` when the user sets different limits for a text-heavy audience.

| Rule | Severity | Meaning |
|---|---|---|
| `no-headline` | error | slide has no heading (or no title placeholder in a .pptx) |
| `duplicate-headline` | error | same headline as an earlier slide |
| `too-many-lines`, `too-many-words` | error | over the limits above |
| `missing-notes` | error | no notes on a main slide (dividers and appendix excepted) |
| `chart-no-source`, `multiple-charts`, `image-no-alt` | error | chart and image rules |
| `font-too-small` | error | explicit text size under 12 pt in a .pptx |
| `headline-topic` | warning | no verb found, or a stock label such as Overview or Next steps |
| `headline-long`, `notes-thin`, `notes-long` | warning | over 15 words; under 25 or over 220 words |
| `font-below-body-size` | warning | explicit non-source text under 18 pt in a .pptx |

The title slide (slide 1 with two body lines or fewer), divider slides with no body, and appendix slides are exempt from the topic-headline check. If Python is not available, check the same table by hand, slide by slide.

## Limits

- `headline-topic` is a word-list check for a verb, not grammar. It misses topic headlines that happen to contain a listed verb and flags some real takeaways. Read the headline spine yourself.
- A .pptx check sees only explicit font sizes; sizes inherited from the template are invisible to it. Image and chart descriptions are checked for presence, not for quality, and the .pptx chart source check only looks for a "Source:" line on the slide.
- The script does not check facts, colour contrast, overflow, overlap or how the deck looks. Render and look.
- The thresholds are working values for a live 16:9 talk, not measured optima. Read-ahead decks and teaching decks may justify higher limits; state the change.
- Template, brand and theme design are out of scope; use the user's template as given.
