---
name: image-prompt-direction
description: Writes and lints image-generation prompts like an art director, using an eight-field contract (subject, composition, lens, lighting, palette, style, negatives, aspect ratio). Use when the user says write an image prompt, prompt for a hero image, product photo prompt, why do my AI images look generic, or fix this prompt. A script flags missing fields, living-artist, trademark and real-person likeness terms, contradictory terms and bad aspect ratios. Do not use for editing existing images, video prompts, logo design, or imitating a named living artist or a real person.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the checklist in step 5 by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Image prompt direction

Turn a brief into a prompt that any text-to-image generator can follow, and keep it free of rights problems. Vendor-neutral: no generator-specific syntax except where a flag is named as optional.

## The prompt contract

Every prompt states eight fields. Write them as labelled lines in a plain text file, one field per line, so the script can read and diff them.

| Field (label) | Must say | Weight |
|---|---|---|
| Subject | who or what, count, age or material, action | 20 |
| Composition | shot size, camera angle, where the subject sits in the frame, what is in front and behind | 15 |
| Camera/lens | focal length or lens type, depth of field. For non-photographic styles write the equivalent (flat, isometric) or `none` | 10 |
| Lighting | source, direction, quality (soft or hard), time of day | 15 |
| Palette | three to five named colours or one colour relationship | 10 |
| Style | medium plus finish or era, described. Never a maker's name | 15 |
| Negative | what must not appear, as nouns | 5 |
| Aspect ratio | numeric, for example `4:5` | 10 |

Required fields: subject, composition, lighting, style, aspect ratio. Pass bar: score 70 or more and no error. Weights and the bar are working values, not measured optima.

Example lines: `Lighting: soft window light from the left, late morning, gentle shadows` and `Camera/lens: 85mm prime, f/2, shallow depth of field`. For term effects, read [references/vocabulary.md](references/vocabulary.md) only when choosing lens, lighting or composition terms.

## Workflow

```
- [ ] 1 Extract the brief into the eight slots
- [ ] 2 Ask only for what is missing (maximum 3 questions)
- [ ] 3 Choose the aspect ratio from the destination
- [ ] 4 Translate every named reference into a description
- [ ] 5 Write the labelled prompt file and lint it
- [ ] 6 Report
```

1. **Extract.** Fill each field from the brief. Mark a slot `ASSUMED` in your notes when you invented it, and say so in the report.
2. **Ask.** If subject, destination or intended mood is missing, ask, at most three questions, in that order of priority. Do not ask about lens or palette; choose them and report the choice.
3. **Aspect ratio by destination:** website hero 16:9 or 21:9; social feed portrait 4:5; story or reel cover 9:16; square avatar or thumbnail grid 1:1; blog header 3:2 or 16:9; print portrait 2:3 or 3:4; ultra-wide banner 21:9 or 3:1. Beyond 4:1 or 1:4 no mainstream generator accepts the shape. If the target generator supports a fixed list only, say which ratio you rounded to.
4. **Translate references.** A mood board item, a favourite artist or a brand becomes a description of what is visible: line weight, palette, grain, era, material, camera. Table:

| Brief says | Write instead |
|---|---|
| "like [living illustrator]" | the line quality, palette and finish you can see in their work, for example `thin even ink lines, flat gouache fills, limited warm palette` |
| "looks like [celebrity]" | an invented person: age range, build, hair, clothing, expression |
| "Disney or Pixar look" | `soft rounded 3D character forms, warm bounce light, saturated storybook palette` |
| "[brand] logo on it" | drop it, or leave an empty blank area for the user to add the real mark later |
| "[famous photographer] style" | the lighting and framing: `hard side light, deep black shadows, centred symmetrical portrait` |

5. **Write and lint.** Save the prompt as labelled lines, then run `python scripts/prompt_lint.py lint prompt.txt`. Read the JSON. Fix every `error`; fix each `warning` or say why it stays. Re-run until `verdict` is `pass`. Do not edit the script to make a check pass.
6. **Report** in the shape below.

## Iteration rules

An image that misses is fixed by changing exactly one field, so the cause is known.

1. Generate at least 4 images per prompt version before judging; one image is noise.
2. Name the miss in one sentence, map it to the field that controls it (wrong mood: lighting or palette; cluttered: composition or negative; looks flat or fake: camera/lens or style), and change only that field.
3. Save each version as its own file (`v1.txt`, `v2.txt`) and run `python scripts/prompt_lint.py diff v1.txt v2.txt`. If `ok` is false, two or more fields changed: split the change into two versions.
4. If the generator exposes a seed, keep it fixed while iterating one field.
5. After 5 versions with no improvement, stop and reopen the brief: the goal, not the wording, is usually the problem.

## Rights rules

- No living artist's name, in any form (`in the style of`, `by`, `inspired by`). Describe the look. The script flags a documented list as an error and unknown capitalised names after style words as a warning.
- No real person's name or likeness, no face swaps, no celebrity lookalikes. Characters are invented.
- No trademarks, franchise characters, logos or branded products unless the user states that they own them; then run `lint ... --allow "<term>"` and record the reason in the report.
- A clean lint is not clearance. The lists in [references/rights-lists.md](references/rights-lists.md) are examples; a name not on them is still a problem. Tell the user that rights questions for commercial use belong to their counsel.

## Report

```
Prompt file: <path>   Score: <n>/100   Verdict: <pass|revise|blocked>
Assumed: <slots you invented>
Translated: <references replaced by descriptions>
Warnings kept: <code and reason>
Not checked: <e.g. how the target generator renders it; any rights beyond the lists>
```

## Scripts

- `scripts/prompt_lint.py lint <file> [--allow TERM]`: run it. Strict JSON: fields found, score, findings (code, severity, line, match, message), verdict. Exit 0 only on `pass`.
- `scripts/prompt_lint.py diff <old> <new>`: run it. Strict JSON listing changed fields; `ok` true when at most one changed. Needs labelled files.

Exit 2 with a plain message on a missing, empty or unreadable file. Finding codes are listed in [references/rights-lists.md](references/rights-lists.md) under "Finding codes".

## Limits

- English only; keyword detection of unlabelled fields is approximate, so use labelled lines.
- Contradiction rules cover 12 common pairs; a deliberate pair (a photograph of a painting) is flagged and should be rewritten as one clear object.
- One prompt per file. Negative-prompt syntax differs by generator; this skill writes a `Negative:` line and leaves vendor flags to the user.
- The script cannot see the image. A passing lint means the prompt is complete and consistent, not that the output will be good.
- The rights lists are short and illustrative; they miss names, and flag some ordinary words (for example `Frozen` as a franchise).
