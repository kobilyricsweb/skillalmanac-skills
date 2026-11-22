## Contents

- How to read this table
- Limits table
- Link handling
- Hashtag norms
- Image ratios
- Sources and confidence

# Platform limits, stated as of 2026-11-21

Platforms change these numbers without notice. Every row carries a confidence level. When a row matters to the job (a long post near the cap, a hashtag count), re-check the platform's own help page before publishing and pass the corrected number to the script with `--limits`.

## How to read this table

- Text limits count what the post shows, including spaces, emoji and hashtags. The script counts Unicode code points; an emoji built from several code points (flags, skin tones, family emoji) counts as more than one there, which errs on the safe side.
- "Fold" is the number of characters shown before the feed cuts the post with a "more" link. It is approximate and changes with device width. The hook and any disclosure belong before it.
- "House recommendation" is the editorial default of this skill, not a platform rule.

## Limits table

| Platform | Text cap | Fold (approx.) | Hashtag hard limit | House recommendation | Confidence |
|---|---|---|---|---|---|
| X (free account) | 280 | none (long posts exist only on paid tiers, up to 25,000) | none stated; script errors above 10 (house value, verify (unconfirmed, as of 2026-11)) | 0 to 2 | high for 280 and the paid-tier size; rest unconfirmed |
| LinkedIn post | 3,000 | about 210 (verify (unconfirmed, as of 2026-11)) | 30 (script; verify (unconfirmed, as of 2026-11)) | 3 to 5, at the end | high for 3,000; fold and hashtag cap unconfirmed |
| Instagram caption | 2,200 | about 125 (verify (unconfirmed, as of 2026-11)) | verify (unconfirmed, as of 2026-11): 30 in most guides, 5 in a few recent ones | 3 to 5 | high for 2,200; hashtag cap unconfirmed |
| Facebook post | 63,206 (verify (unconfirmed, as of 2026-11)) | about 125 (verify (unconfirmed, as of 2026-11)) | no practical cap (verify (unconfirmed, as of 2026-11)) | 0 to 3 | unconfirmed |
| Threads post | 500 | none | one topic tag per post is the intended use (verify (unconfirmed, as of 2026-11)) | 1 | high for 500; tag rule unconfirmed |
| Bluesky post | 300 | none | no stated cap | 0 to 2 | high for 300 (tool vendors say characters; the platform counts graphemes) |
| TikTok caption | 4,000 (verify (unconfirmed, as of 2026-11); 2,200 until recently) | about 90 (verify (unconfirmed, as of 2026-11)) | no practical cap (verify (unconfirmed, as of 2026-11)) | 3 to 5 | unconfirmed |
| YouTube description | 5,000 (title 100) (verify (unconfirmed, as of 2026-11)) | about 100 (verify (unconfirmed, as of 2026-11)) | 15 (above 15 the platform ignores all of them; verify (unconfirmed, as of 2026-11)) | 3 | unconfirmed |

The Instagram hashtag cap: several 2026 tool-vendor pages still say 30, a few say Instagram moved to 5 in December 2025, and no platform help page was found to settle it. The script therefore errors only above 30 and warns above 5. If your account shows the 5 limit, run with `--limits` setting `instagram.hashtags_max` to 5.

## Link handling

| Platform | Rule to apply |
|---|---|
| X | Every link counts as 23 characters whatever its real length. The script applies this. |
| LinkedIn | Real URL length counts. Put the link at the end of the post body, after the point has been made; do not rely on "link in the first comment", which is common advice but was not tested here. |
| Instagram | Links in captions are not clickable. Send readers to the profile link or a story link sticker; write the destination in words ("link in profile"). |
| Facebook | Link previews are generated from the page's Open Graph tags; fix the page, not the post. |
| Threads, Bluesky | Real URL length counts; link cards are generated from the page. |
| TikTok, YouTube | TikTok captions are not a click path; YouTube descriptions are, and the first link sits in the visible window. |

## Hashtag norms

Put hashtags last, never inside a sentence on X, LinkedIn or Bluesky. Use specific tags a reader would search for, not a generic pile. A tag that is also a disclosure (`#ad`) goes first, not last (see writing_rules.md). Script codes: `hashtag_count` is an error above the hard limit; `hashtag_count_high` is a warning above the house recommendation.

## Image ratios

Every ratio below is verify (unconfirmed, as of 2026-11) except where marked high by multiple sources; check the platform's help page before exporting.

| Use | Ratio to export | Confidence |
|---|---|---|
| Instagram feed, portrait | 4:5 | high |
| Instagram feed, square | 1:1 | high |
| Instagram Reels, TikTok, YouTube Shorts | 9:16 | high |
| LinkedIn single image | 1.91:1 or 1:1 | medium |
| X in-feed image | 16:9 or 1:1 | medium |
| Facebook link preview | 1.91:1 | medium |
| Bluesky image | 1:1 to 16:9 | low |

Keep key content inside the central 80 percent: crops differ between feed, grid and preview. The script does not check images.

## Minimum posting gaps

The script's per-platform `min_gap_minutes` values (X 120, LinkedIn 720, Instagram 480, Facebook 480, Threads 180, Bluesky 120, TikTok 480, YouTube 1440) are editorial working values, not platform rules: verify (unconfirmed, as of 2026-11). Override with `--min-gap-minutes` or `--limits`.

## Sources and confidence

Checked with a web search on 2026-11-21 (secondary sources, not the platforms' own pages):

- Buffer, character limits per network: https://support.buffer.com/article/588-character-limits-for-each-social-network
- Metricool, guidelines and limits: https://help.metricool.com/en/article/character-limit-for-each-social-network-4ivf8t/
- Ayrshare, character limits reference: https://www.ayrshare.com/docs/help-center/technical-support/character-limits.md
- Metricool, Instagram limits in 2026: https://metricool.com/instagram-limits/
- Sendible, Instagram character limit: https://www.sendible.com/insights/instagram-character-limit

These sources support: X 280 free and 25,000 on paid tiers, X links counted as 23, LinkedIn 3,000, Threads 500, Bluesky 300, Instagram caption 2,200 with a conflict on hashtags. Facebook, TikTok and YouTube numbers, all folds and all image ratios are the author's working knowledge and were not re-verified.
