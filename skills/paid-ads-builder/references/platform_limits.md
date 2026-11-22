## Contents

- How to read this table
- Character limits and asset counts
- Where to confirm each number
- Counting rules

## How to read this table

Every number is "verify (unconfirmed, as of 2026-11)": written from memory of the platforms' public ad specifications, not re-read from a live ad manager on that date. Kind "hard" means the platform rejects or truncates the text, and the validator reports an error. Kind "display" means the text is accepted but cut in the feed, and the validator reports a warning. If the live ad manager disagrees, trust the ad manager and put the real number in the plan's `limit_overrides`.

## Character limits and asset counts

| Platform | Field | Limit | Kind | Status |
|---|---|---|---|---|
| Google search (responsive ad) | Headline | 30 | hard | verify (unconfirmed, as of 2026-11) |
| Google search | Description | 90 | hard | verify (unconfirmed, as of 2026-11) |
| Google search | Display path (each of 2) | 15 | hard | verify (unconfirmed, as of 2026-11) |
| Google search | Headlines per ad | 3 to 15 | hard | verify (unconfirmed, as of 2026-11) |
| Google search | Descriptions per ad | 2 to 4 | hard | verify (unconfirmed, as of 2026-11) |
| Microsoft search (responsive ad) | Headline | 30 | hard | verify (unconfirmed, as of 2026-11) |
| Microsoft search | Description | 90 | hard | verify (unconfirmed, as of 2026-11) |
| Meta feed ad | Primary text, visible before "see more" | 125 | display | verify (unconfirmed, as of 2026-11) |
| Meta feed ad | Headline, visible | 40 | display | verify (unconfirmed, as of 2026-11) |
| Meta feed ad | Link description, visible | 30 | display | verify (unconfirmed, as of 2026-11) |
| LinkedIn single image ad | Intro text, visible | 150 | display | verify (unconfirmed, as of 2026-11) |
| LinkedIn single image ad | Headline, visible | 70 | display | verify (unconfirmed, as of 2026-11) |
| LinkedIn single image ad | Description, visible | 100 | display | verify (unconfirmed, as of 2026-11) |
| TikTok in-feed ad | Ad text | 100 | hard | verify (unconfirmed, as of 2026-11) |

Other search-specific rules the validator applies: no exclamation mark in a search headline, no repeated punctuation, no two or more all-caps words. These are common disapproval reasons rather than limits.

## Where to confirm each number

Open the ad creation screen for the format and read the counter beside the field; this is the authority. For the written specification, search the platform's own help centre for the ad format name plus "specs" (Google Ads Help, Microsoft Advertising Help, Meta Business Help Centre, LinkedIn Marketing Solutions, TikTok Ads Help). Record the date you confirmed it.

## Counting rules

- The validator counts Python characters (code points). A letter with an accent counts as 1; many emoji count as 1 here but 2 on some platforms. Keep 2 characters of spare room on any headline that contains an emoji or a symbol.
- Dynamic insertion tokens (keyword insertion, location insertion) expand at serve time. Write the longest likely value into the text when counting.
- Spaces and punctuation count.
