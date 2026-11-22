---
name: alt-text-writer
description: Writes and reviews image alt text and long descriptions in HTML and Markdown. Use when the user asks for alt text, image descriptions for accessibility, an alt text review, or says screen reader users cannot tell what an image is. Sorts images as informative, decorative, functional, complex or text-in-image, applies length and context rules, and runs a script flagging missing, file-name, generic, over-long and repeated alt, empty alt on linked images and charts lacking a long description. Do not use for whole-page WCAG audits, caption writing, image generation prompts, or describing an image nobody has described to you.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual checks in step 1 and step 6.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Alt text writer

Decide what each image is for on its page, then write the alt text that does that job. The text is judged by what a person who cannot see the image needs in order to follow the page, not by how completely the picture is described.

## Rule zero: you cannot see the image

The script reads markup, never pixels. You usually cannot see the picture either. Never write alt text for an image from its file name, its surrounding text alone, or a guess. For every image that needs new text, get two facts from the user: what it shows, and why it is on this page. If the user cannot say, leave the image listed as unresolved. Do not invent people, names, emotions, ages, colours or numbers.

## Workflow

```
- [ ] 1 Inventory: run the script, read every flag
- [ ] 2 Ask the user once, as a batch, about images that need facts
- [ ] 3 Classify each image with the function table
- [ ] 4 Write alt text with the rule for its function
- [ ] 5 Write long descriptions for complex images
- [ ] 6 Verify with --described, apply, re-run on the page
- [ ] 7 Report
```

1. **Inventory.** Run `python scripts/alt_text_review.py <page-or-folder>`. Each image gets a `function_guess`, `flags`, and `needs_user_description` with a question in `ask`. Without Python, list every image tag or Markdown image by hand and check each against the flag table below.
2. **Ask once.** Group the questions from `ask` into a single message, one line per image with its file and line number. Accept short answers. Do not start writing text for images the user has not answered about.
3. **Classify.** Use the function table. The same file can have a different function on a different page, so classify per use, not per file.
4. **Write** the alt text, one image at a time, using the rule, length and context sections. Keep the user's words for names, product terms and numbers. For before and after examples per function and Markdown patterns, read the matching section of [references/alt-text-examples.md](references/alt-text-examples.md); it also lists the standards pages behind the rules.
5. **Long descriptions** for complex images follow the long-description section.
6. **Verify.** Put every proposal into a descriptions file (shape under Script contract), run `python scripts/alt_text_review.py <page> --described descriptions.json`, fix every proposal with `ok: false`, and apply the proposals to the page. Run the script again on the edited page and clear the remaining flags or explain each one. Do not edit the script to make a check pass.
7. **Report** in the fixed shape at the end.

## Function table

| Function | How to tell | Alt rule | Test question |
|---|---|---|---|
| Informative | A photo, drawing or screenshot that adds meaning the nearby text does not give | A short phrase giving what matters about it in this context | If the image failed to load, what would the reader lose? Say that. |
| Decorative | Spacer, divider, background flourish, pure mood picture, icon next to a text label that says the same | `alt=""` and nothing else. In Markdown, an empty bracket pair after the exclamation mark | Remove it: does the page lose any information? If no, it is decorative. |
| Functional | Image is the only content of a link or button, or an image map area, or an image submit button | The action or destination, not the picture: "Search", "See pricing", "Download the 2025 report (PDF)" | What happens when it is activated? Say that, in 1 to 5 words. |
| Complex | Chart, graph, diagram, infographic, map, flowchart, dense screenshot | Short alt: type, subject and the main takeaway. Then a long description, visible on the page or linked | Can the point be said in 125 characters while the data cannot? Then it is complex. |
| Text in image | Banner, logo, quote card, poster, sign | The exact text, word for word. A logo gets the organisation name, plus "home" when it links home | Would a reader who cannot see it miss the words? Then repeat them. |

If the text beside the image already says everything, make the image decorative. Saying it twice costs a screen reader user time and gains nothing.

## Length table

| Situation | Target | Notes |
|---|---|---|
| Functional image | 1 to 5 words, about 30 characters | Name the action; no "link" or "button" |
| Icon or small informative image | 1 to 8 words | |
| Typical informative photo | about 40 to 80 characters | One clause: who or what, doing what |
| Photo that carries the story | up to 125 characters | One or two short sentences |
| Complex image | 125 characters or fewer for alt | Everything else goes in the long description |
| Over 125 characters | flagged, not forbidden | The script flags it. Keep it only if it truly cannot be shorter. |
| Over 250 characters | move the text out of alt | Visible text under the image, a caption, or a linked page |

The 125-character figure is a working limit used by many checkers, not a number in WCAG. The script takes `--max-length` if a team uses a different one. Do not end an alt with filler to reach a length, and do not cut mid-meaning to meet it.

## Context rules

1. **Purpose beats appearance.** The same portrait of a chief executive is "Maria Lopez, chief executive" on her profile, "Maria Lopez presenting the 2025 results" in a results story, and empty when her name and role are printed right next to it.
2. **Do not repeat the neighbours.** If the caption or the paragraph already carries the information, use `alt=""` or add only what they lack. The script flags an alt that matches the adjacent caption.
3. **Linked images.** Alt names the destination or action. If a text link beside the image goes to the same place inside one link, the image alt is empty. An empty alt as the only content of a link leaves the link with no name; the script flags it.
4. **Same image, many places.** Same file and same purpose gets the same alt each time. Different images must not share an alt on one page; the script flags that.
5. **Galleries and product shots.** Each image names what is different about it: the colour, the angle, the model. Not "Product photo" ten times.
6. **Screenshots.** Name the screen and the point being made, not every control: "Billing settings with the Cancel plan button highlighted". If numbered steps in the text already walk through the screen, keep the alt short.
7. **People.** Use names, roles and actions the user supplied. Do not state age, gender, ethnicity, mood or disability unless the page itself says it and it matters to the point.
8. **Emails, slides and social posts.** Same rules; the field is called alt text or description in most editors. Where the platform has no field, put the description in the visible text.
9. **Generated alt from a template.** If alt is built from a variable such as the product title, the script marks it `dynamic_alt` and skips text checks. Review the template once and spot-check real output.

## What not to say

| Avoid | Why | Instead |
|---|---|---|
| "Image of", "picture of", "photo of" | Screen readers already announce an image | Start with the content. Keep "photo" or "painting" only when the medium is the point |
| File names, `IMG_4821.jpg`, hashes | Carries no meaning | What it shows |
| "Image", "photo", "graphic", "logo" alone | Names a kind of thing, not this one | The specific subject or the organisation name |
| "Click here", "link to" | The role is announced; the label should be the action | "See pricing" |
| Keyword lists for search | Reads as noise to a listener and does not help the person | One honest phrase, SEO or not |
| The caption again | Heard twice | `alt=""`, or only the extra detail |
| "Decorative", "spacer", "divider" as the alt text | Announces junk | `alt=""` |
| Guesses ("looks happy", "probably a team") | Unverified claims presented as fact | Only what the user told you |
| A title attribute instead of alt | Not reliably read, not a replacement | Write alt; drop title unless it adds a tooltip the user wants |

## Long descriptions for complex images

Use one when the image carries more than a short alt can: any chart with more than three values, any diagram with relationships, any infographic.

1. State the purpose in one sentence ("This chart compares sign-ups by month to show the June jump").
2. Give the main finding first.
3. Give the data in full, as a table for numbers or a list for steps. For a diagram, list the parts in reading order, then how they connect.
4. Add the axes, units, date range and the source.
5. Place it so a person can reach it: visible text next to the image (best, helps everyone), a `<details>` block, or a link such as "Description of the sign-ups chart" right after the image. In HTML, point `aria-describedby` at the id of the visible text. Do not rely on the old `longdesc` attribute.
6. In Markdown, put the description under the image under a heading or inside `<details>`.

The script counts a long description as present when it finds any of: `longdesc`, an `aria-describedby` target that exists on the page, a figure caption of 60 characters or more (in Markdown, an emphasised or "Figure 1" or "Source:" line directly under the image), a `<details>` block in the 800 characters after the image, or wording such as "long description", "data table", "described below" or "transcript" there. Phrase the nearby text so the check can see it.

## Script contract

Run it, do not edit it. It writes nothing; stdout is strict JSON.

`python scripts/alt_text_review.py PATH [PATH ...] [--max-length N] [--described FILE]`

Scans `<img>`, `<input type=image>`, `<area href>` and Markdown images, including reference style, skipping fenced and inline code in Markdown. Exit 0 no findings, 1 findings, 2 bad input (message on stderr starting with `error:`).

Output keys: `schema_version`, `max_alt_length`, `files_scanned`, `images_total`, `images_flagged`, `needs_user_description`, `counts_by_flag`, `images[]`, `proposals[]`, `unmatched_descriptions[]`, `verdict`, `not_checked`.

Each `images[]` entry: `file`, `line`, `kind`, `src`, `alt` (null when the attribute is missing), `title`, `dynamic_alt`, `context` (`heading`, `in_link`, `in_figure`, `caption`), `function_guess`, `flags[]`, `detail`, `needs_user_description`, `ask`, `described`, `proposal_alt`.

| Flag | Meaning |
|---|---|
| `missing_alt` | No alt attribute |
| `empty_alt_in_link` | Empty alt, and nothing else names the link or button |
| `title_without_alt` | Title present, alt missing or empty |
| `filename_alt` | Alt looks like a file or camera name, or equals the file stem |
| `generic_alt` | Alt is a placeholder word such as image, photo, logo |
| `redundant_prefix` | Starts with "image of", "photo of" and similar |
| `long_alt` | Longer than `--max-length` (default 125) |
| `repeated_alt` | Same alt on different images in one file |
| `caption_duplicate` | Alt matches the adjacent caption (similarity 0.85 or more) |
| `decorative_candidate` | File name, class or 1 by 1 size suggests decoration but alt has text |
| `presentation_role_with_alt` | `role=presentation` or `aria-hidden` with non-empty alt |
| `complex_no_long_description` | Chart-like image with no sign of a long description |

`function_guess` is a heuristic from the file name, class, link context and alt. Treat it as a question for the user, never as a verdict.

Descriptions file: `{"images": [{"src": "...", "function": "informative|decorative|functional|complex|text_in_image", "shows": "...", "purpose": "...", "alt": "...", "long_description_location": "...", "text": "...", "text_also_on_page": true}]}`. `src` matches the page's src or its file name. `long_description_location` is required for complex images. `text` is required for text-in-image. Each `proposals[]` entry has `flags[]` and `ok`. Proposal flags: the alt flags above plus `alt_on_decorative`, `empty_alt_for_<function>`, `functional_alt_names_role_or_picture`, `complex_without_long_description`, `text_not_verbatim`, `text_field_missing`.

## Report format

```
Images: <n> total, <n> fixed, <n> left decorative, <n> unresolved
Changed: <file:line, function, new alt in quotes>, one line each
Long descriptions: <image, where it lives>
Needs the author: <images the user could not describe, with the question>
Script: <verdict before> -> <verdict after>, remaining flags and why they stay
Not checked: whether any alt matches the real picture; SVG and CSS background images; the live site
```

## Limits

- The script cannot judge whether alt text is true. It checks form, not accuracy.
- Heuristics (decorative candidates, complex images, function guess) use file names, classes and nearby words, and will miss images with uninformative names and flag a few honest ones.
- Long description detection is wording-based; a description phrased unusually may be missed.
- SVG elements, CSS background images, icon fonts, canvas and video poster images are not scanned.
- Template placeholders are skipped, so rendered pages need a spot check.
- The 125-character limit and the 0.85 caption similarity are working values, not standards.
- English wording lists only. The writing rules apply in any language; the generic-word and prefix checks do not.
- This skill writes and checks alt text. A whole-page accessibility review is a different job.
