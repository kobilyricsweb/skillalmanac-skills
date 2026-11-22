---
name: brand-guidelines-kit
description: Use when the user asks for a brand book, brand guidelines, style guide, brand voice guide, or a palette and fonts a team or freelancer can follow. Writes the document (positioning statement, voice and tone table, logo rules, colour roles with contrast pairs, type scale, imagery rules, templates) and validates a brand tokens JSON with a script for bad hex, missing roles, text pairs under WCAG 4.5:1, duplicate colours and a non-growing type scale. Do not use for UI component libraries or code design tokens, logo or name creation, trademark advice, or ad copy.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, compute the contrast ratios by hand with the formula in references/brand-rules.md.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Brand guidelines kit

Turn what the user knows about their business into a guideline document that a stranger (a freelancer, a new hire, a printer) can follow without asking. The deliverable is a Markdown document plus a `brand-tokens.json` that passes the checker.

## Rule zero: no invented facts

Audience, competitors, mission, existing colours, fonts and logo files come from the user. If a fact is missing, write `[needs input: <what>]` in the document and list it in the report. Taste choices (palette, fonts, voice words) may be proposed, but are marked "proposed" until the user confirms. Never claim a trademark, font licence or colour is cleared.

## Workflow

```
- [ ] 1 Intake: ask only for what is missing
- [ ] 2 Positioning statement
- [ ] 3 Voice and tone table
- [ ] 4 Palette and brand-tokens.json
- [ ] 5 Run the checker, fix, re-run
- [ ] 6 Type, logo, imagery, templates
- [ ] 7 Assemble and report
```

1. **Intake.** Needed: what the business sells and to whom, 3 competitors or comparable brands, what exists already (logo file types, colours, fonts), where the brand appears (web, print, social, packaging). Ask in one message, not one question per turn. Proceed with `[needs input]` for anything unanswered.
2. **Positioning statement**, one sentence in this exact contract, then a one-line test result:
   `For <specific customer> who <need or situation>, <brand> is the <category people already understand> that <single main benefit>, because <proof that can be checked>. Unlike <named alternative>, <one real difference>.`
   Fail the statement if: the customer is "everyone" or "businesses"; the benefit is an adjective ("high quality", "innovative"); the proof cannot be checked by a stranger; a competitor could sign it unchanged. Rewrite until none applies, or flag it `[needs input: proof]`.
3. **Voice and tone.** Pick 3 voice traits, each as "X but not Y" with both ends being real options ("plain but not curt"). A trait that nobody would reject ("professional", "friendly") is not a trait. Then a table, one row per trait, plus a tone-by-situation block:

   | Trait | We sound like | We do not sound like | Do (example line) | Don't (example line) |
   |---|---|---|---|---|

   Every Do and Don't is a full sentence on the user's own subject, never a slogan. Tone shifts by situation, not by trait: give one line each for celebration, routine info, bad news, error or outage, and complaint reply. Bad news and errors drop humour and exclamation marks first.
4. **Palette.** Roles, not swatches. Required roles: `primary`, `background`, `text`. Normally also `text-muted`, `surface`, `on-primary`, `accent`, and `success`, `warning`, `danger` if the product shows status. Give each colour a name, a hex (`#RRGGBB`) and a role in `brand-tokens.json` (shape below). Start from `assets/brand-tokens.template.json`. Prefer 1 primary, at most 1 accent, 3 to 5 neutrals; more than 8 colours in total is a flag to cut.
5. **Check.** Run the script, fix every error, re-run until `"ok": true`. Warnings are read and either fixed or named in the report. Never edit the script or the thresholds to make it pass; change the colours instead. Contrast pairs in the report go into the document's palette table.
6. **Type, logo, imagery, templates.** Use the numbers in the next section. Do not invent a logo; if no logo file exists, write the rules as conditional on the supplied file.
7. **Assemble** in this fixed order and give the file a title and date:
   1 Positioning statement; 2 Voice and tone; 3 Logo; 4 Colour (roles table, contrast table from the checker); 5 Typography; 6 Imagery; 7 Templates; 8 Open items (every `[needs input]`). A section with nothing confirmed still appears, with its open items.

## Defaults to apply (numbers an agent tends to omit)

- **Logo clear space:** at least the height of the logo's own mark or initial letter ("x") on all four sides; larger for print than screen. State the unit as that proportion, not as pixels.
- **Logo minimum size:** give two values, print (mm width) and screen (px width), and name the smallest-size variant if one exists. If unknown, write `[needs input: minimum size]` after testing the supplied file at small size; do not guess.
- **Logo misuse list:** at minimum 8 items: stretch or squash; rotate; recolour outside the palette; add shadows, outlines or gradients; rearrange or resize parts; place on a background below 3:1 contrast with the logo (or without the supplied reversed version); crop; set on a busy photo without a plate.
- **Contrast:** body text and small text 4.5:1 against its background, large text (about 24 px regular or 18.66 px bold, which is 18 pt and 14 pt bold) 3:1, interface component boundaries and icons 3:1. The checker enforces 4.5:1 on every listed or default text pair unless a pair is marked `"size": "large"`.
- **Type scale:** 3 to 6 steps listed smallest to largest, each at least a minor second (ratio 1.067) above the last, a ratio of about 1.2 to 1.25 for text-heavy brands and 1.333 to 1.5 for display-led ones; body at 16 px or more; at most 2 families (one may be a system font stack); give weights by role (regular body, semibold heading). Give line height per step (about 1.5 for body, 1.1 to 1.25 for large headings) and a fallback stack for each family.
- **Imagery:** rules written as testable statements: subject, crop, colour treatment (for example "natural light, no filter, max 1 brand colour overlay at 60% or less"), what is banned (stock handshake, 3D-render people, text baked into photos), alt-text rule (describe the content, 125 characters or fewer, no "image of"), and where illustrations are allowed instead of photos.
- **Templates list** (for the document's section 7): name each template, its format, its owner who edits it, and what may change: business card, email signature, letterhead, slide deck, social post (square and 9:16), invoice, one-page sell sheet, social avatar and cover. Only list what the user uses.

## brand-tokens.json contract

```
{"brand": "Name",
 "colors": [{"name": "Ink", "hex": "#111827", "role": "text"}],
 "pairs": [{"foreground": "Ink", "background": "Paper", "size": "normal", "use": "body"}],
 "type_scale": [{"name": "body", "size": 16}],
 "spacing": [4, 8, 16]}
```

`pairs` is optional. Without it the script checks every `text` and `text-muted` colour against every `background` and `surface` colour, and `on-primary` against `primary`. `size` is `normal` (needs 4.5) or `large` (needs 3). Colour names match case-insensitively. `type_scale` has at least 3 steps, smallest first. `spacing` is optional, ascending.

## Script

`scripts/brand_tokens_check.py check <tokens.json>`: run it, do not edit it. Prints strict JSON (no NaN, ASCII only): `ok`, `errors`, `warnings`, `findings` (each with `severity`, `code`, `path`, `message`) and `contrast_pairs` (each with `ratio`, `required`, `pass`). Exit 0 no errors, 1 errors, 2 file or JSON problem.

Error codes: `invalid_hex`, `duplicate_color`, `duplicate_name`, `missing_role`, `missing_color_role`, `missing_colors`, `low_contrast`, `type_scale_not_monotonic`, `missing_type_scale`, `bad_type_step`, `bad_spacing`, `spacing_not_ascending`, `bad_pair`, `pair_unknown_color`. Warning codes: `unknown_role`, `body_too_small`, `type_step_too_close`, `spacing_off_grid`.

Read [references/brand-rules.md](references/brand-rules.md) when writing the logo, imagery or tone sections, or when no Python is available (it holds the contrast formula and a worked example). Use [assets/brand-tokens.template.json](assets/brand-tokens.template.json) as the starting tokens file.

## Report

```
Document: <path>   Tokens: <path>
Checker: <ok true/false, errors, warnings, and what each warning was resolved to>
Proposed (needs confirmation): <palette, fonts, voice traits the user did not supply>
Open items: <every [needs input]>
Not checked: <logo files, font licences, trademark status, print colour conversion, real-world rendering>
```

## Limits

- The checker validates numbers, not taste. A palette can pass and still look wrong; a human must look at it.
- Contrast is computed from sRGB hex on flat colours. Text over images, gradients, transparency, dark-mode variants and colour-blind simulation are not checked.
- Pass at 4.5:1 is the WCAG 2.x minimum for text, not a guarantee of readability; WCAG 3 style (APCA) scoring is not used.
- It does not create or edit logos, fonts or image files, and does not check licences or trademarks.
- Print specifics (CMYK, Pantone) are not converted; ask the printer or a designer.
- Thresholds such as the 1.067 step ratio and the 4 px grid are working values, reported as warnings only.
- For UI components, spacing systems in code, or design tokens for engineers, use a design-system skill instead.
