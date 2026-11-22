---
name: programmatic-video
description: Produces and checks videos built from code or data (Remotion, ffmpeg, moviepy). Use when the user wants a video rendered from a script, spreadsheet or template, batch or auto-captioned videos, a data video or slideshow, or a render with drift, cut-off text or missing media. Sets a composition contract, a timeline JSON, asset and license rules and render settings per destination, then runs a QC pass; a script flags overlapping clips, clips past the end, missing files, long or too-fast captions and fps or resolution mismatches. Do not use for scripts and channel strategy, GUI editor work, or AI-generated footage.
license: Apache-2.0
compatibility: The checker needs Python 3.9 or newer, standard library only, no network. Rendering needs the user's own tool (for example ffmpeg or a Node-based renderer); this skill never installs one. Without Python, do the manual pass in step 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Programmatic video

Make a video from code or data in a way that can be checked before the slow render. The order is: contract, timeline file, assets, validation, draft render, final render, QC. Write the contract and timeline first; renderer code comes second and reads them.

## Workflow

```
- [ ] 1 Write the composition contract
- [ ] 2 Write timeline.json
- [ ] 3 Collect and describe assets
- [ ] 4 Run the checker, fix, re-run
- [ ] 5 Draft render, then final render
- [ ] 6 QC the output file
- [ ] 7 Report
```

1. **Composition contract.** Ask for the destination if not given, then fix these five values in one place (a `composition` object) and never override them per clip: fps, width x height, duration in seconds, safe margin, caption style (max characters per line 42, max lines 2, max 17 characters per second, 1.0 to 7.0 s on screen). Defaults when the user has none: 30 fps, 1920x1080 landscape or 1080x1920 vertical, safe margin 5 percent on every edge. Use 24, 25, 30, 50 or 60 fps only; keep source and composition on the same family (25 with 50, 30 with 60, 24 alone) because mixing 25 and 30 makes judder. Destination values: [references/render-targets.md](references/render-targets.md); read only the row you need.
2. **Timeline file.** One JSON file, times in seconds, shape below. Tracks hold clips; a track is one lane, so two clips on it must not overlap unless the track sets `"allow_overlap": true` (use that only for deliberate crossfades). Captions are clips on a `caption` track with a `text` field. Put every start on a frame boundary: `round(seconds * fps) / fps`.
3. **Assets.** Rules, all enforced by the checker where a field exists:
   - Music and fonts must carry a `license` (name and where it came from). No license text, no asset. Unknown provenance means do not use it and tell the user.
   - File names lowercase, digits, dash, underscore, no spaces (`bed-track.mp3`); paths relative to the project root, forward slashes, no `..`.
   - Record `fps`, `width`, `height`, `duration` for every video asset and `duration` for audio. Read them from the file with `ffprobe -v error -show_entries stream=width,height,r_frame_rate,duration -of json <file>` rather than guessing; `r_frame_rate` is a fraction such as `30000/1001` (29.97).
   - Fonts: embed or install the exact file you declared; a renderer that silently falls back to another font changes line breaks and breaks the caption limits.
4. **Check.** Run, fix every error, re-run until `"ok": true`:

```bash
python scripts/timeline_check.py timeline.json
python scripts/timeline_check.py timeline.json --strict   # warnings also fail
```

   Warnings are decisions: fps mismatch (frames dropped or repeated), resolution mismatch (scaled; a different aspect ratio crops or adds bars), off-frame start, caption too short or long, unused asset. Fix or state why each stays. Run the script; do not edit it to make a check pass. Without Python, check by hand in this order: overlaps per track, every end <= composition duration, every path exists, every caption line <= 42 characters and <= 17 characters per second, every asset fps and size against the composition.
5. **Render.** Draft first: first 5 seconds (or one clip) at half resolution, to catch layout and font problems in under a minute. Then the final with the destination row from the render-targets table. A final render that was not preceded by a clean check run is not allowed.
6. **QC the output file** (a file, not the timeline). Each item has a pass rule:
   - Container duration within 1 frame of the composition duration (`ffprobe -show_entries format=duration`).
   - Video stream fps and size equal the contract; pixel format `yuv420p` for broad playback; audio stream present when the timeline has audio.
   - Sync: pick 3 caption start times (first, middle, last), extract a frame at each (`ffmpeg -ss <t> -i out.mp4 -frames:v 1 f.png`) and confirm the right caption is visible; for speech, the caption appears no more than 0.2 s before the word and no later than 0.1 s after (house tolerance, not a standard).
   - Overflow: no text outside the safe margin in those frames; no line wrapped differently from the planned two-line form.
   - Missing media: no black or still-frame stretch where a clip should play (sample one frame per clip).
   - Audio: no clipping, speech readable over music; loudness target per destination.
7. **Report** in this fixed shape:

```
Contract: <fps, size, duration, destination>
Checker: <ok true/false, errors, warnings and what was done about each>
Render: <command or tool, output file, size, duration>
QC: <each item above: pass, fail, or not checked>
Left for the user: <licenses to confirm, values marked verify, anything unrendered>
```

## Timeline shape

```json
{
  "composition": {"fps": 30, "width": 1920, "height": 1080, "duration": 20,
                  "safe_margin_pct": 5,
                  "captions": {"max_line_chars": 42, "max_lines": 2, "max_cps": 17}},
  "assets": {
    "intro": {"type": "video", "path": "assets/intro.mp4", "fps": 30, "width": 1920, "height": 1080, "duration": 12, "license": "own footage"},
    "bed":   {"type": "audio", "path": "assets/bed-track.mp3", "duration": 180, "license": "CC0, library track 114"},
    "head":  {"type": "font",  "path": "assets/headline-sans.ttf", "license": "SIL OFL 1.1"}
  },
  "tracks": [
    {"id": "v1", "kind": "video", "clips": [{"id": "c1", "asset": "intro", "start": 0, "duration": 12, "source_in": 0, "speed": 1}]},
    {"id": "a1", "kind": "audio", "clips": [{"id": "m1", "asset": "bed", "start": 0, "duration": 20, "source_in": 30}]},
    {"id": "cap", "kind": "caption", "clips": [{"id": "k1", "start": 1, "duration": 3, "text": "Line one\nLine two", "font": "head",
                                                "box": {"x": 200, "y": 880, "w": 1520, "h": 120}}]}
  ]
}
```

Track `kind`: `video`, `audio`, `caption`, `overlay`. Asset `type`: `video`, `audio`, `image`, `font`. A clip has `start` plus `duration` (or `end`); `source_in` and `speed` (default 1) are used to check that the clip does not run past the source file. `box` is in pixels and is checked against the safe margin. A caption box outside it is an error; for other clips it is a warning.

## Checker output

`scripts/timeline_check.py` prints one strict JSON object (no NaN, no comments) and nothing else: `command`, `ok`, `strict`, `summary` (`errors`, `warnings`, `tracks`, `clips`, `assets`), `findings` (each with `level`, `code`, `where`, `message`). Exit 0 ok, 1 findings fail, 2 unusable input (missing or empty file, invalid JSON, NaN, duplicate keys; then `ok` false and a `fatal` message). Options: `--root DIR` (asset base, default the timeline's folder), `--strict`, `--max-line-chars N`, `--max-lines N`, `--max-cps N` (command line beats the composition, which beats the defaults).

| Level | Codes |
|---|---|
| error | `E_SCHEMA` `E_OVERLAP` `E_BEYOND_DURATION` `E_MISSING_ASSET` `E_PATH_ESCAPE` `E_UNKNOWN_ASSET` `E_NO_LICENSE` (audio, font) `E_TRIM_BEYOND_SOURCE` `E_CAPTION_LINE_LENGTH` `E_CAPTION_TOO_MANY_LINES` `E_CAPTION_TOO_FAST` `E_CAPTION_OUTSIDE_SAFE_AREA` |
| warning | `W_FPS_MISMATCH` `W_RESOLUTION_MISMATCH` `W_OFF_FRAME_GRID` `W_CAPTION_SHORT` `W_CAPTION_LONG` `W_NO_LICENSE` (video, image) `W_ASSET_NAME` `W_BACKSLASH_PATH` `W_NO_FPS` `W_NO_DIMENSIONS` `W_NO_DURATION` `W_KIND_MISMATCH` `W_OUTSIDE_SAFE_AREA` `W_UNUSED_ASSET` |

If the user already has another timeline format (a Remotion props file, an EDL, a moviepy script), write a small converter to this shape rather than changing the checker.

## Boundaries

- Licensed media only. Do not rip music or footage from streaming or video sites, and do not strip watermarks or content IDs. If the user has no license, suggest their own recordings or libraries whose terms they have read.
- Do not generate a person's likeness or voice for a real individual without that person's permission.
- The skill checks structure and timing. It does not judge whether a video is good, accurate or allowed on a platform.

## Limits

- The checker validates the timeline file, not the rendered video. Step 6 is a manual pass with the user's own tools.
- It checks only the metadata fields written in the file; wrong metadata gives a wrong pass. It checks that a path is a file, not that it is a valid media file.
- Caption speed counts characters, not words, and does not know the language; 17 characters per second is a starting value for Latin text and is too fast for some languages and too slow for others.
- Variable-frame-rate sources are reported at their average rate; transcode them to constant frame rate first.
- Every platform figure in the render-targets reference is marked `verify (unconfirmed)` unless stated otherwise: they were written from memory of public guidance and not re-read when the skill was written. Check the destination's current page before a final render.
- The checker does not model transitions, effects, nested compositions or audio levels.
