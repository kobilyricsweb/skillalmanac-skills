# Listing page content: programmatic-video

**One line:** Plan, validate and QC videos rendered from code or data, with a timeline checker that fails before the slow render.

## What it does

The skill gives an agent a fixed order for producing a video programmatically: a composition contract (fps, size, duration, safe margin, caption limits), a timeline JSON, asset and license rules, a draft then final render, and a QC pass on the output file. `scripts/timeline_check.py` validates the timeline before any render and prints strict JSON. A reference table lists codec, size, bitrate and loudness starting points per destination, each marked `verify (unconfirmed)` where the figure was not re-read from the platform.

## Capabilities

- Timeline checker: clips overlapping on one track, clips past the composition end, missing asset files, trim past the source length, captions over the line, line-count or characters-per-second limits, captions outside the safe margin, asset fps and resolution against the composition, missing licenses on music and fonts
- Fixed timeline schema and a frame-rate family table
- Render command patterns for ffmpeg and a per-destination settings table
- A QC procedure with pass rules (duration, fps, sync frames, overflow, missing media, audio)
- A fixed report: contract, checker result, render, QC, items left for the user

## When to use

You want an agent to produce a video from a script, spreadsheet or template with Remotion, ffmpeg, moviepy or similar, in batches or with generated captions, or a render has drifting captions, cut-off text or missing media.

## When not to use

Writing the script, hook or channel plan (that is content work, see `youtube-content-kit`); working in a GUI editor; generating footage with AI video models; audio-only editing. This skill covers building and checking the video file. It does not install or run a renderer for you.

## Requirements

Python 3.9 or newer for the checker (standard library only, no network). A renderer of the user's choice for the render step; ffmpeg and ffprobe are used in the example commands.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved agent output. What exists is the checker on the saved fixtures (`python evals/run_fixtures.py`, 8 of 8 cases pass).

1. `python scripts/timeline_check.py evals/fixtures/bad.json --root <folder with the existing assets>`: exit 1, 10 errors and 3 warnings, among them `E_OVERLAP` (clips c1 and c2 overlap by 1 s), `E_TRIM_BEYOND_SOURCE`, `E_BEYOND_DURATION` (clip ends at 11 s in a 10 s composition), `E_CAPTION_LINE_LENGTH` (48 characters, limit 42), `E_CAPTION_TOO_FAST` (21 characters in 1 s), `E_CAPTION_OUTSIDE_SAFE_AREA`, `E_MISSING_ASSET`, `E_NO_LICENSE`, `E_UNKNOWN_ASSET`, `W_FPS_MISMATCH` (25 fps in a 30 fps composition).
2. `python scripts/timeline_check.py evals/fixtures/good.json --root <folder with the assets>`: exit 0, `"ok": true`, 0 errors, 0 warnings, 3 tracks, 6 clips, 4 assets.

## Limits

- The checker validates the timeline file, not the rendered video; the QC pass is manual with the user's own tools.
- It trusts the metadata written in the file and checks only that a path is a file.
- Caption speed counts characters, not words, and is tuned for Latin text.
- Platform figures are unconfirmed and must be checked before a final render.
- Transitions, effects, nested compositions and audio levels are not modelled.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN, and 8 script fixture cases pass with hand-derived expectations. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review, any real render.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Give the agent a brief (vertical 15 s recap, three scenes, four captions); it writes the contract and `timeline.json`.
2. Run the checker: `W_FPS_MISMATCH` for the 25 fps chart clip; the agent explains its decision.
3. Introduce a caption that is too long; the checker returns `E_CAPTION_LINE_LENGTH`; the agent splits it and re-runs to `ok: true`.
4. Draft render, then QC: frames extracted at three caption times; the report lists what was not checked.

## FAQ seeds

- Does it need network access? No. The checker uses only the standard library.
- Does it render the video? No. It plans, validates and guides the render with your own tool.
- Does it work with Remotion or moviepy? It is renderer-neutral; convert your props or script to the timeline shape once.
- How is it different from `youtube-content-kit`? That skill plans scripts, hooks and channel content; this one produces and checks the video file.
- Are the platform bitrate numbers reliable? They are marked `verify (unconfirmed)`; check the platform page before the final render.
- Will it use any song I give it? No. Music and fonts need a license entry, and ripped or unlicensed media is declined.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
