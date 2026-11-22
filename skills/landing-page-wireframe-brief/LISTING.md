# landing-page-wireframe-brief

## One line

Turns a short intake (offer, audience, one primary action, three or more benefits) into a six-section wireframe brief for one landing page, with a TO-SUPPLY list for every fact the page still needs.

## What it does

The skill follows a fixed eight-step procedure. It checks four required intake fields first. If any is missing, it stops and returns a numbered question list instead of a plan. When intake is complete, it writes the goal as one sentence, locks the primary action to the Hero and Final call buttons, and orders six sections: Hero, Proof, Benefits, How it works, FAQ and Final call.

Each section row gives a purpose, the content needed, an element type, a word budget and a phone-width note. Benefits are used exactly as the user wrote them, one card each. Anything the intake does not supply, such as reviews, customer counts, logos, plan steps or FAQ answers, is listed as a numbered TO-SUPPLY row rather than filled in. The output ends with a status: complete when nothing is missing, partial when a brief exists with open items, and blocked when no brief could be written.

## When to use

Use it when a landing page needs a content plan before a designer opens a design tool, for example a service page for a small business, a course enrollment page or a product waitlist. It suits teams that have the offer and the benefits but no agreed section order, word budget or list of missing material.

## When not to use

Do not use it to write final headlines or body copy, to choose colors and typefaces, to build the page in code, or to plan a multi-page site. It also does not create proof. If the user wants testimonials, counts or logos, the skill records them as open items and never supplies placeholders that look real.

## Requirements

A text-capable agent. No tools, no network, no files beyond the skill folder. The user supplies the intake in the conversation.

## Example

Input (intake as given by the user): offer "small-group online math tutoring for high school students"; audience "parents of high school students who need help with algebra and geometry"; primary action "Book a free 30-minute trial lesson"; benefits "small groups of four students", "tutors certified in each subject", "a progress report every two weeks". No proof, no FAQ facts, no steps, no brand name supplied.

Output:

# Wireframe brief: Small-group online math tutoring

Status: partial

## Goal and primary action
Goal: Visitors leave having booked a free 30-minute trial lesson.
Primary action: Book a free 30-minute trial lesson

## Intake check
| Field | Status |
|---|---|
| Offer | Present |
| Audience | Present |
| Primary action | Present |
| Benefits | Present (3) |

## Section order
| # | Section | Purpose | Content needed | Element type | Word budget | Mobile note |
|---|---|---|---|---|---|---|
| 1 | Hero | State the offer and the trial lesson in one glance | Headline (6 to 12 words) naming the offer and audience; subhead naming the three benefits; brand name (TS-01) | Headline, subhead, primary button, image slot | 40 | Primary button sits directly below the subhead, above the image slot |
| 2 | Proof | Show that other families have used the service | No proof supplied (TS-02 to TS-04) | Logo row or quote cards | 30 | Logos in a grid of two per row |
| 3 | Benefits | Explain why small groups and certified tutors matter | Card 1: small groups of four students. Card 2: tutors certified in each subject. Card 3: a progress report every two weeks | Three cards: icon slot, heading, one line | 100 | Cards stack in the same order as desktop |
| 4 | How it works | Show the path from trial lesson to enrolled student | Three steps not supplied (TS-05 to TS-07) | Three numbered steps | 60 | Steps stack vertically, numbered |
| 5 | FAQ | Answer the questions parents ask before booking | Four answers not supplied: price, lesson length, cancellation terms, schedule or location (TS-08 to TS-11) | Accordion with 4 questions | 250 | Accordion, all questions collapsed on load |
| 6 | Final call | Repeat the single action after the reader has seen the detail | Headline and primary button using the Hero action | Headline and primary button | 30 | Button sits directly below the headline |

## TO-SUPPLY
| ID | Section | Item needed | Why it blocks the page |
|---|---|---|---|
| TS-01 | Hero | Brand name for the header and the headline | The page has no name to show the reader |
| TS-02 | Proof | Parent or student reviews, with name, date and permission to publish | Proof row cannot be filled without real quotes |
| TS-03 | Proof | Customer count or result statistic, with its source and date | A number on the page needs a source before it can be published |
| TS-04 | Proof | School or partner logos, with written permission to use them | Logos cannot be shown without permission |
| TS-05 | How it works | Step 1 of 3, in the user's words | The section needs three real steps |
| TS-06 | How it works | Step 2 of 3, in the user's words | The section needs three real steps |
| TS-07 | How it works | Step 3 of 3, in the user's words | The section needs three real steps |
| TS-08 | FAQ | Answer on price, with the exact fee | FAQ answers need the real terms |
| TS-09 | FAQ | Answer on lesson length | FAQ answers need the real terms |
| TS-10 | FAQ | Answer on cancellation and refund terms | FAQ answers need the real terms |
| TS-11 | FAQ | Answer on schedule or location | FAQ answers need the real terms |

## Limits

The word budgets and mobile values are working values. They are a starting point for a designer, not a published standard. The skill does not check accessibility, search ranking or conversion. It produces one page only, and it cannot confirm that a benefit is true or that a proof item is real. The user is responsible for every fact in the intake.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
