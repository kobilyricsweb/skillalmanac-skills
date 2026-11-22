## Contents

- Where the numbers come from
- What a missing DPI means
- Format advice heuristic
- Sources

# Header facts used by the script

Read this when a reported number looks wrong or you must check a file by hand.

## Where the numbers come from

| Format | Dimensions | Density | Truncation check |
|---|---|---|---|
| PNG | IHDR chunk, first 8 data bytes after the signature | pHYs chunk: pixels per metre, unit byte 1; dpi = value x 0.0254 | chunk walk must reach IEND |
| JPEG | first start-of-frame marker (SOF0 to SOF15 except a few non-frame codes) | JFIF APP0 units 1 (dots per inch) or 2 (per cm, x 2.54); units 0 is only an aspect ratio. EXIF XResolution with ResolutionUnit 2 or 3 is the fallback | an end-of-image marker in the last 2 KB |
| GIF | logical screen width and height, little-endian, bytes 6 to 9 | none | last byte is the 0x3B trailer |
| WebP | lossy VP8 frame header, lossless VP8L header, or the extended VP8X canvas | none read | RIFF length plus 8 must not exceed the file size |
| SVG | `width` and `height` attributes converted to px (pt 4/3, pc 16, in 96, cm and mm by 96 per inch); `viewBox` when they are missing or relative | none | a closing svg tag near the end |

SVG is vector, so the script reports its size but skips exact-pixel checks and compares only the aspect ratio. Animated WebP and GIF are read at canvas size; frame sizes are not checked.

## What a missing DPI means

`dpi: null` means no density was found in the places above. The file may still carry one in a place the script does not read (Photoshop resource blocks, XMP). Density metadata does not change pixels: a 1748 x 2480 file prints at A5 only if 300 dpi is the intended density, and `max_print_size_in` in the result shows the print size those pixels support at the spec's minimum.

## Format advice heuristic

Bytes per pixel is file size divided by width x height. JPEG is treated as photographic. PNG and GIF at 1.0 or more, and WebP at 0.3 or more, are treated as photographic. Everything else, and SVG, is treated as a flat graphic. This is a hint from file size, not a look at the artwork: when the guess is wrong, trust the image.

- Photographic content: JPEG or WebP, then PNG only when the spec demands it.
- Flat graphics, logos, text: PNG or lossless WebP. JPEG smears edges and often is larger.
- If the current format is already the best allowed one, the advice is `keep_format_tune`: lower quality in small steps or reduce colours, and only then pixels.

## Sources

Facts above are restated in the author's words from these public specifications:

- PNG chunk layout and pHYs: https://www.w3.org/TR/png-3/
- JPEG file interchange (JFIF density units): https://www.itu.int/rec/T-REC-T.871
- GIF89a logical screen descriptor and trailer: https://www.w3.org/Graphics/GIF/spec-gif89a.txt
- WebP container (RIFF, VP8, VP8L, VP8X): https://developers.google.com/speed/webp/docs/riff_container
- SVG viewBox and length units: https://www.w3.org/TR/SVG2/coords.html
