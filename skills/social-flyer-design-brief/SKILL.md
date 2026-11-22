---
name: social-flyer-design-brief
description: Writes a short design brief for a social post, flyer or slide before any design tool is opened. It sets the primary message, a copy deck with character budgets, two layout options in words and an export checklist. Use when someone has a graphic to make from a blank canvas and needs copy, hierarchy and sizes settled first, such as a bake-sale flyer or an event post. Do not use for drawing artwork, inventing brand colours, logos or fonts, or confirming a specific design tool's features.
license: Apache-2.0
compatibility: none beyond a text-capable agent.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Design brief before the blank canvas

Turn a request for a social post, flyer or slide into a brief that a person can execute in any design tool. The brief is the only deliverable. Do not produce artwork, image prompts, colour picks for unsupplied brands, or steps that depend on one tool's menus.

All numbers below are working values chosen for this procedure. They are not industry standards, except the WCAG contrast ratios in step 5, which are published.

## Workflow

Run the steps in order. Each step has one required output. Ask for missing intake fields in a single message of at most 8 questions.

### Step 1. Intake

Required output: the Intake table with one row per field.

| Field | Required | If missing |
|---|---|---|
| Goal (inform, sell, recruit, thank) | yes | ask |
| Audience | yes | ask |
| Format (social post, story, flyer, slide) | yes | ask |
| Size and ratio | yes | use the default in Table 1 and mark it "default" |
| Key message (one sentence) | yes | ask |
| Mandatory text (date, time, place, price, contact or link) | yes | ask; copy exactly as given, never retype |
| Brand colours and fonts | no | write "not supplied"; never invent |
| Images | no | write "none supplied" |

Table 1. Default size per format (working sizes)

| Format | Default size | Max text levels |
|---|---|---|
| Social post | 1080 x 1080 px square | 2 |
| Story | 1080 x 1920 px vertical | 3 |
| Flyer | US Letter, 8.5 x 11 in | 3 |
| Slide | 1920 x 1080 px, 16:9 | 3 |

### Step 2. Primary message and hierarchy

Required output: one sentence starting "The primary message is", plus the count of text levels used.

Rules:
- Exactly one primary message. If the intake holds two, ask which one leads.
- L1 is the headline, L2 the supporting line, L3 every detail (date, place, price, contact, call to action).
- Mandatory details are L3 unless the key message itself is a detail.
- Total words must stay under the Table 2 limit.

Table 2. Word limit per format

| Format | Max total words | Max text levels |
|---|---|---|
| Social post | 25 | 2 |
| Story | 30 | 3 |
| Flyer | 60 | 3 |
| Slide | 40 | 3 |

### Step 3. Copy deck with character budgets

Required output: the Copy deck table. Count characters including spaces and punctuation. A draft that exceeds its budget must be shortened and the status set to "trimmed".

Table 3. Default character budgets per block (working values)

| Block | Level | Social post | Story | Flyer | Slide |
|---|---|---|---|---|---|
| Headline | L1 | 30 | 30 | 40 | 50 |
| Support line | L2 | 50 | 50 | 70 | 80 |
| Detail (date, time, place, price) | L3 | 40 | 40 | 90 | 60 |
| Call to action | L3 | 20 | 20 | 30 | 30 |
| Handle or link | L3 | 25 | 25 | 40 | 40 |

Rules: a block with no supplied text is written as "[to supply]" and its status is "open". Never write a price, date or contact that the user did not give.

### Step 4. Two layout options in words

Required output: exactly two options, each at most 80 words. The options must differ in anchor position.

Each option states these five fields:
1. Reading order (for example: headline, support, detail, call to action).
2. Anchor: headline in top third, centre, or bottom third, and left, centre or right.
3. Image zone: share of the area, from 0 to 100 percent. Use 0 percent when no image was supplied.
4. Detail block: placement in top, middle or bottom third.
5. Empty space: at least 20 percent of the area stays empty (working value).

### Step 5. Contrast check

Required output: one line per colour pair, or the line "contrast not checked, colours not supplied".

Threshold table (WCAG 2.x ratios, published):

| Text size | Minimum contrast ratio |
|---|---|
| Under 24 px regular, or under 18.66 px bold | 4.5 to 1 |
| Large text (24 px regular or larger, or 18.66 px bold or larger) | 3 to 1 |

Do not choose colours for the user. Report pass or fail only for colours the user supplied.

### Step 6. Export checklist

Required output: a checklist, one line per item, with the size and file type taken from the intake or from Table 1.

Default file types: PNG for social post and story, PDF for flyer and slide.

Checklist items:
- Size and ratio match the intake.
- Every mandatory string matches the copy deck character for character.
- No text sits within 5 percent of any edge (working value).
- The headline is readable at thumbnail size (about 10 percent of the short side, working value).
- File name pattern: slug, format, version, extension, for example `bake-sale_flyer_v1.pdf`.

### Step 7. Open questions

Required output: a list of at most 5 items naming every field marked "not supplied" or "open" that the user has not answered.

## Output contract

Use these headings in this order. Put nothing else before the first heading except an optional one-line title.

1. `## Intake` with the Step 1 table.
2. `## Primary message` with one sentence.
3. `## Copy deck` with the table columns: Block | Level | Budget | Draft | Count | Status (fits, trimmed or open).
4. `## Layout options` with `### Option A` and `### Option B`, each listing the five fields from Step 4.
5. `## Contrast` with the Step 5 output.
6. `## Export checklist` with the Step 6 checklist.
7. `## Open questions` with the Step 7 list.

## Refuse or stop when

- The key message and the mandatory text are both missing and the user will not supply them: stop after step 1 and return the intake table only.
- The user asks for brand colours, a logo, fonts, photos, testimonials or reviews that were not supplied: refuse those items and write "not supplied".
- The user asks whether a named design tool has a feature: say this skill is tool-neutral and do not confirm or deny the feature.
- The copy would state medical, financial or legal results (cures, guaranteed returns, "best in town" with no source): stop and ask for the source.
- The user asks to reproduce third-party text, a photo or a logo: stop and ask for permission or an original.
- The user asks for more than 3 text levels or more than 2 layout options: deliver 3 levels and 2 options and state the limit in Open questions.

## Files in this package

- `SKILL.md`: this procedure.
- `LICENSE.txt`: Apache-2.0 text.
- `evals/trigger_queries.json`: prompts that should and should not trigger this skill.
- `evals/evals.json`: one offline task with pass criteria.
