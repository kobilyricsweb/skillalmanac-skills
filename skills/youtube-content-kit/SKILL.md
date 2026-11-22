---
name: youtube-content-kit
description: Turns a video idea into a script outline with a 15-second hook, a chapter list, title, description, tags, a thumbnail brief and a publishing checklist, then validates the package with a script (hook word count, 3+ chapters with increasing timestamps, title and description limits, tag count, sponsorship disclosure). Use when the user wants a YouTube script, video outline, chapters, title ideas, description, tags, thumbnail concept, or asks if a video is ready to publish. Do not use for general social posts (use a social content skill), video editing, channel analytics, or titles that promise things the video does not deliver.
license: Apache-2.0
compatibility: The validator needs Python 3.9 or newer, standard library only, no network. Without Python, follow the manual check table in step 7.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# YouTube content kit

Produces one video package: script outline, chapters, metadata, thumbnail brief, checklist. Then checks it with `scripts/video_check.py`. The numbers below are working heuristics unless marked as a platform limit.

## Rules the package must follow

1. **One promise.** Write it as one sentence: "After this video the viewer can / knows / has ___." Title, hook, thumbnail and chapters all serve that sentence. Two promises means two videos.
2. **Hook of at most 15 seconds**, which is at most 37 spoken words at 150 words per minute (the script fails above 37, warns above 30). The hook states the promise and the proof it is real; it does not greet, introduce the channel or ask for a subscribe.
3. **Pattern break at least every 30 seconds** (heuristic, not a platform rule): a cut to a new visual, graphic, demo, location, music change or a new question. List the planned break seconds in the package.
4. **No clickbait.** The title and thumbnail may only promise what the video shows. Every claim in the title must be paid off inside the video, and the chapter where it is paid off is named in the checklist. No invented urgency, no fake reaction faces for events that did not happen, no "you won't believe" framing.
5. **Disclosure when sponsored** (see below). Never optional, never moved into a link-only line.

## Workflow

```
- [ ] 1 Brief: promise, viewer, length, sponsor yes/no, primary keyword
- [ ] 2 Hook and outline
- [ ] 3 Chapters
- [ ] 4 Title, description, tags
- [ ] 5 Thumbnail brief
- [ ] 6 Build package.json (assets/package_template.json)
- [ ] 7 Validate, fix, re-run
- [ ] 8 Publishing checklist and report
```

1. **Brief.** Ask only for what is missing: the one-sentence promise, who watches, target length, whether any part is paid or gifted, and the primary keyword (the phrase a viewer would search). If the user gives only a topic, propose the promise and keyword and say you did.
2. **Hook and outline.** Hook order: result or question (one line), proof it is real (one line), what the video does in what order (one line). Then 3 to 7 sections. For each: the one point, the proof or demo, and the planned pattern break. Put the strongest payoff of the promise by the 40 to 60 percent mark, not the final minute. End by pointing to one next video, not a list of five.
3. **Chapters.** Timestamps as `0:00` or `1:05:30`. The first is `0:00`; at least 3; each at least 10 seconds long (platform rule); titles describe the content in 2 to 6 words, no teasers. If the real edit does not exist yet, mark times as planned and say they must be replaced after the edit.
4. **Title, description, tags.** Title: promise and keyword in the first 60 characters (hard limit 100). Offer 3 options with different angles (how-to, result, question) and recommend one. Description: first 150 characters hold the keyword and the promise in plain words, no link, no "subscribe" opener; then chapters, then links, then sponsor and affiliate lines, then hashtags (up to 3). Tags: 3 to 15, total under 500 characters including separators, no hash sign, add common misspellings of hard names; treat tags as minor.
5. **Thumbnail brief.** Fill the fields in [references/video-rules.md](references/video-rules.md) section "Thumbnail brief". Hard facts: 16:9, 1280 by 720 pixels recommended, under 2 MB. The thumbnail must show something that appears in the video.
6. **Build the package** from `assets/package_template.json`: title, hook (spoken text only), script (full spoken text if available), description, primary_keyword, tags, chapters, duration_s, pattern_breaks, sponsored, disclosure.
7. **Validate.** Run and fix until `"ok": true`, then read every WARN:

```bash
python scripts/video_check.py package.json
```

Do not edit the script to make a check pass. Exit 0 means no FAIL; exit 1 means at least one FAIL; exit 2 means bad input. Without Python, check by hand:

| Check | Pass condition |
|---|---|
| Hook | at most 37 words |
| Chapters | 3 or more, first 0:00, strictly increasing, 10 s apart at least |
| Title | at most 100 characters, about 60 visible |
| Description | keyword in first 150 characters, at most 5,000 |
| Tags | at most 500 characters in total |
| Sponsored | disclosure in description, in the script, and the platform's paid-promotion setting on |

8. **Publishing checklist and report.** Give the package, then this fixed report:

```
Promise: <one sentence>
Validator: <ok true/false; FAIL and WARN counts; each WARN kept or fixed>
Payoff check: <title claim -> chapter that delivers it>
Disclosure: <not sponsored | where disclosed>
Placeholders: <planned timestamps, unknown duration, missing links>
Not checked: <facts in script, music/footage rights, platform policy changes, real retention>
```

## Sponsorship and disclosure

If any part of the video is paid, gifted, affiliate-linked or in-kind: say so aloud near the start, before the first sponsored mention, and again at the segment; show it on screen; put "Sponsored by ..." or "Paid promotion" in the first 150 characters of the description; turn on the platform's paid-promotion setting. Affiliate links get their own plain line ("These are affiliate links; I earn a commission"). Disclosure rules differ by country and are the creator's responsibility; the script checks presence, not legal sufficiency. Details and source links: [references/video-rules.md](references/video-rules.md).

## Scripts

- `scripts/video_check.py <package.json | ->`: run it. Prints strict JSON with `ok`, `counts`, `hook_words`, and `findings` (severity FAIL or WARN, check name, message). Errors are also JSON.
- `assets/package_template.json`: copy and fill it.

## Limits

- Hook length is counted in words at a fixed pace; a slow or fast speaker changes the real seconds.
- The 30-second pattern-break rule, 60-character title view and 15-tag advice are heuristics. Platform limits (100-character title, 5,000-character description, 500-character tags, 3 chapters, 10-second chapters, 2 MB thumbnail) can change; recheck them.
- The script cannot judge whether a title is honest. It flags a short list of stock clickbait phrases; the payoff check in step 8 is a human judgment.
- It does not check facts, rights to music or footage, or legal disclosure sufficiency in any country.
- It cannot predict views or retention. Treat the structure as a starting hypothesis and compare with the channel's own retention graph.
- Scope is long-form planning. Short-form clips and cross-platform posts are a different job.
