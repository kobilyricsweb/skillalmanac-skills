# Render targets

Status of every figure below: **verify (unconfirmed)** unless the cell says "stable". "Unconfirmed" means written from memory of public guidance and not re-read when this skill was written. Platforms change limits without notice; open the source page for the destination before the final render and update the numbers you use.

Sources to check (pages, not quoted here):
- YouTube upload encoding guidance: https://support.google.com/youtube/answer/1722171
- Instagram Reels and TikTok creator help pages: search the platform's help centre for "video specifications"
- ffmpeg documentation for H.264 encoding and the `-movflags` option: https://trac.ffmpeg.org/wiki/Encode/H.264

## Per destination

| Destination | Container and video codec | Size and fps | Video bitrate guide | Audio | Notes |
|---|---|---|---|---|---|
| YouTube, landscape | MP4, H.264 (stable: widely accepted) | 1920x1080, 24 to 60 fps, keep source fps | about 8 Mbps at 30 fps, about 12 Mbps at 60 fps; verify (unconfirmed) | AAC-LC, 48 kHz stereo, 128 to 384 kbps; verify (unconfirmed) | Put `moov` first with `-movflags +faststart`. Re-encoded anyway; do not over-spend bitrate |
| YouTube Shorts | MP4, H.264 | 1080x1920, 30 fps; verify (unconfirmed) | about 8 to 10 Mbps; verify (unconfirmed) | AAC 48 kHz | Maximum length changes over time; verify (unconfirmed) |
| Instagram Reels | MP4, H.264 | 1080x1920, 30 fps; verify (unconfirmed) | about 5 to 8 Mbps; verify (unconfirmed) | AAC 44.1 or 48 kHz | Keep text clear of the top and bottom interface zones: leave about 12 percent top and 20 percent bottom for vertical; verify (unconfirmed) |
| TikTok | MP4 or MOV, H.264 | 1080x1920, 30 fps; verify (unconfirmed) | about 5 to 8 Mbps; verify (unconfirmed) | AAC | Right-side button column and bottom caption zone cover content; verify (unconfirmed) |
| Web page or docs (looping) | MP4 H.264 plus a WebM VP9 alternative; verify (unconfirmed) | width as laid out, 30 fps | CRF 23 to 28 | none for silent loops; strip the audio track | Provide poster frame; keep under a few MB |
| Archive master | MOV or MKV; ProRes or high-quality H.264; verify (unconfirmed) | the contract values | CRF 12 to 16 for H.264 | PCM or AAC 320 kbps | Keep the timeline file and assets with it |
| Draft preview | MP4, H.264 | half the contract size, same fps | CRF 30, `-preset veryfast` | AAC 96 kbps | For layout checks only |

## Command patterns (ffmpeg)

Final, quality-targeted (CRF mode; bitrate then follows the content):

```
ffmpeg -i in.mp4 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -ar 48000 -movflags +faststart out.mp4
```

Bitrate-targeted (when a destination states a cap): replace `-crf 18` with `-b:v 8M -maxrate 10M -bufsize 16M`.

Draft: `-vf scale=iw/2:ih/2 -preset veryfast -crf 30 -t 5`.

Stable facts used above: `yuv420p` is the most widely decoded pixel format; lower CRF means higher quality and a larger file; `-movflags +faststart` moves the index to the front for progressive playback; H.264 needs even width and height.

## Loudness

Many streaming destinations normalise speech-and-music mixes toward about -14 LUFS integrated; verify (unconfirmed). Safe working rule: speech around -16 to -14 LUFS, true peak no higher than -1 dBTP, music bed 12 to 18 dB under speech while someone talks. Measure with the user's tool (for example ffmpeg's `loudnorm` filter in analysis mode); this skill has no loudness script.

## Frame-rate families

| Source fps | Composition fps that stays clean | Avoid |
|---|---|---|
| 24 or 23.976 | 24 | 30 (3:2 judder) |
| 25 | 25 or 50 | 30 |
| 29.97 or 30 | 30 or 60 | 25 |
| 50 | 50 | 30 |
| 59.94 or 60 | 60 or 30 | 24, 25 |

Treat 23.976, 29.97 and 59.94 as the fractions 24000/1001, 30000/1001 and 60000/1001; the checker accepts a 0.1 fps difference as equal, so 29.97 against 30 (or 23.976 against 24) does not raise `W_FPS_MISMATCH`. Decide deliberately whether the project is 30 or 29.97 and use that number everywhere.
