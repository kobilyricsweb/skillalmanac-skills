# YouTube content kit

## One-line summary

Turns a video idea into script outline, chapters, metadata, thumbnail brief and checklist, then validates it.

## What it does

The agent fixes one promise sentence, writes a hook of at most 15 seconds (37 words), plans a pattern break at least every 30 seconds, builds chapters, a title, a description whose first 150 characters carry the keyword and promise, and tags. It fills a thumbnail brief and ends with a fixed report. A standard-library Python script then checks the package as JSON and prints a strict JSON report.

How it differs from `social-content-kit`: that skill covers posts across social platforms. This one is video-specific: scripts, chapters, YouTube metadata limits, thumbnails and sponsorship disclosure for video.

## Capabilities

- Hook word count against a 15-second limit.
- Chapters: at least 3, first at 0:00, strictly increasing, 10 seconds minimum each.
- Title length (100 hard, about 60 visible), stock clickbait phrase warning, all-caps warning.
- Description: keyword in first 150 characters, no link in the preview, 5,000 limit.
- Tags: 500-character total, duplicates, leading hash, count.
- Sponsored videos fail unless description wording, script wording and the paid-promotion toggle are all present.
- Pattern-break gap warning (heuristic: 30 seconds).

## When to use / when not to

Use for planning or checking a long-form video before recording or upload. Do not use for editing video, channel analytics, short-form clips, cross-platform posts, or for titles that promise what the video does not show.

## Requirements

Python 3.9+, standard library only. No network. Without Python the skill gives a manual check table.

## Install

Copy the `youtube-content-kit` folder into `.claude/skills/` or `.agents/skills/`. Pinned install commands are added at publication.

## Examples

Prompt: "Is my sponsored review ready to upload? Check package.json."

Real output of `python scripts/video_check.py evals/fixtures/sponsored_missing.json` (abridged):

```
"ok": false, "counts": {"fail": 3, "warn": 1}
FAIL disclosure-description  video is sponsored but the description has no disclosure wording
FAIL disclosure-spoken       video is sponsored but the script has no spoken or on-screen disclosure wording
FAIL disclosure-toggle       video is sponsored but disclosure.paid_promotion_toggle is not true
WARN description-short       description is 149 characters; the first 150 are the preview, use them
```

Prompt: "Check this draft package."

Real output for `evals/fixtures/bad.json`: `ok: false`, 7 FAIL and 9 WARN, including `hook-length` ("hook is 59 words (about 23.6 s at 2.5 words/s); the limit is 37 words for 15 s"), `chapters-count` ("2 chapters; at least 3 are required"), `chapter-first` ("first chapter starts at 0:05; it must be 0:00") and `title-length` ("title is 114 characters; the limit is 100").

## Limits

Word-based hook timing; heuristics (30 s pattern breaks, 60-character title view) are not measured optima; platform limits can change; the script cannot judge honesty, facts, rights or legal sufficiency of disclosure; it cannot predict retention.

## Evidence

Static lint 0 FAIL, 0 WARN; 6/6 script fixture cases pass (2026-11-21, Windows 11, Python 3.11). No efficacy, trigger, cross-tool or human review yet. See VERIFICATION.md.

## Demo script (60 to 90 s)

1. Prompt: "Plan an 8-minute rice video, no sponsor." Show the one-sentence promise and a 26-word hook.
2. Show the chapter list and three title options with the chapter that pays off each claim.
3. Run `video_check.py` on a draft package: it fails on a 59-word hook and 2 chapters.
4. Fix and re-run: `"ok": true`. Show the final report with "Not checked".

## FAQ seeds

1. Does it need network? No.
2. Does it upload anything to YouTube? No, it only plans and checks.
3. Is 15 seconds a platform rule? No, it is a retention heuristic; the script converts it to 37 words.
4. Does passing the check make my sponsorship legal? No, it checks presence only.
5. How is it different from social-content-kit? Video-specific.
6. Can it write my whole script? It writes an outline and hook; full text only if you ask.
7. How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft; static and fixture checks only.

## License and authorship

Apache-2.0, Copyright 2026 Global Media Holdings. Drafted by an AI model (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has yet taken place.
