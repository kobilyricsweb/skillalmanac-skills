## Contents

- Hook rules
- No engagement bait
- Disclosure for sponsored posts
- Repurposing atoms
- Cadence defaults

# Writing rules

## Hook rules

The hook is the text before the fold (see platform_limits.md). Apply in order:

1. Open with the most specific true thing in the source: a number, a named result, a decision, a surprising constraint. Prefer "median close time fell from 52 to 31 minutes" to "we learned something big".
2. One idea per post. If the hook needs "and", split it into two posts for two days.
3. No announcement openers: "In this thread", "Excited to share", "Big news". The first words must already be content.
4. A question hook is allowed only when the post answers it within the next two lines.
5. The hook must stand alone; cut at the fold it should still make sense.
6. Never promise what the post does not deliver ("you won't believe", "the one trick").
7. Do not invent a number, quote or result to make a stronger hook. Every figure in a post exists in the source.

## No engagement bait

Do not trade an action for reach. Banned patterns (the script warns on the common ones, code `engagement_bait`):

- "Like if you agree", "share if", "retweet if", "double-tap if"
- "Tag a friend who...", "tag 3 people"
- "Comment YES to get the link" (unless a platform feature really delivers the link and the post says so)
- "Follow for part 2" when part 2 does not exist yet
- "Who else hates...?" pure reaction-farming questions

Allowed: one real question the team will answer, a plain "link in profile", a plain "reply with your case and we will look at it" when someone will. Platforms say they reduce the reach of such posts; the stronger reason is that they train readers to ignore the account.

## Disclosure for sponsored posts

Mark `sponsored: true` for any post where money, a free product, an affiliate commission or a business relationship came with the post. Rules this skill applies:

1. Disclose in the post text, in plain words, before the fold: "Sponsored by X", "Paid partnership with X", "Ad:". The strong markers the script accepts: `#ad`, `#sponsored`, `#paidpartnership`, `#paidpromotion`, `#advertisement`, or those words in the text.
2. Weak tags do not count alone: `#sp`, `#collab`, `#partner`, `#ambassador`, `#gifted`, `#thanks`, `#promo`, `#affiliate`. Advertising regulators have said such tags are not clear enough by themselves.
3. A platform's paid-partnership toggle may be used in addition. It counts as the disclosure in the script only on Instagram, Facebook, TikTok and YouTube, and only when the calendar row says `disclosure: platform_label`. On X, LinkedIn, Threads and Bluesky use text.
4. Never bury the marker in a pile of hashtags at the end of a long caption (`disclosure_not_upfront`).
5. Video and image-only posts need the disclosure in the visible words on the media too; the script checks text only.
6. A reshare of a sponsored post is also sponsored.

The US Federal Trade Commission's guidance on endorsements wants a disclosure that is clear and conspicuous and cannot be missed; the UK Advertising Standards Authority wants an upfront label such as "Ad". This skill is not legal advice; local law and the sponsor's contract may demand more.

- FTC, disclosures for social media influencers: https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers
- UK ASA, recognising ads on social media: https://www.asa.org.uk/advice-online/recognising-ads-social-media.html

Both pages were named from the author's knowledge and not fetched when this skill was written; open them before relying on the wording.

## Repurposing atoms

Before writing any post, pull the source into atoms and write them in a table:

| id | Type | Content (exact figure, quote or claim) | Source location |
|---|---|---|---|
| a1 | number | ... | para 3 |

Types: number, quote, decision, mistake, step, contrast, link. Rules:

1. Aim for 6 to 10 atoms from a 1,000 to 2,000 word source. Fewer than 4 means the source cannot feed a calendar; say so.
2. Each post uses one primary atom. The same atom is not used twice on one platform inside 14 days.
3. The same atom may go to two platforms only in two different forms: a LinkedIn paragraph and an X one-liner, never the same text (`unadapted_cross_post`).
4. Every post carries the source link or names the source when no link fits; quotes keep their speaker.
5. Anything not in the source (a stat from elsewhere, a customer name) needs the user's confirmation and goes in the report under "Needs a source".

## Cadence defaults

Working values for a small team, not measured optima:

| Platform | Posts per source in the first 14 days | Minimum gap |
|---|---|---|
| LinkedIn | 3 | 12 hours |
| X | 5 | 2 hours |
| Instagram | 2 | 8 hours |
| Threads, Bluesky | 3 | 2 to 3 hours |

Spread posts over at least 3 days: day 0 as launch, then days 2, 5, 9 and 13. Times are in the audience's local zone; use the account's own analytics for the best hour when it has them, otherwise 08:30 to 10:30 on weekdays as a neutral start. Always write the UTC offset in `scheduled_at`.
