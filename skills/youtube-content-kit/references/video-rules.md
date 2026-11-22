## Contents

1. Hook patterns
2. Pacing and pattern breaks
3. Title patterns and the honesty test
4. Thumbnail brief
5. Disclosure details
6. Platform limits and sources

## 1. Hook patterns

Pick one; each fits in 37 words or fewer.

| Pattern | Shape | Use when |
|---|---|---|
| Result first | "This <thing> now <result>. Here is exactly how, in <N> steps." | a how-to with a measurable outcome |
| Question with a stake | "Why does <common thing> <surprising effect>? I tested it <how>." | explainers, tests |
| Before/after | show the end state for 3 s, then "that took <time> and <cost>" | builds, edits, repairs |
| Mistake warning | "Most <people> <do X> and lose <thing>. Do this instead." | corrections; only if the claim is true |

Banned in the first 15 seconds: greetings, channel intros, "before we start", sponsor reads (unless the sponsor is the topic), asking for likes. The sponsor line comes after the promise.

## 2. Pacing and pattern breaks

Working heuristic: something visibly or audibly changes at least every 30 seconds. Counts as a change: new shot or angle, on-screen graphic or text, screen recording, B-roll, music shift, a new question put to the viewer, a physical move. A zoom on the same shot does not count alone. Plan a bigger reset (new location, chapter card, recap line) every 2 to 3 minutes. Record planned break seconds in `pattern_breaks`; the validator warns when any gap exceeds 30 seconds. Change the interval only if the user states another one.

## 3. Title patterns and the honesty test

Patterns: how-to ("How to <result> in <time/steps>"), result ("<Thing> <result>: <proof>"), question ("Is <claim> true?"), list with a number only when the video really has that many items.

Honesty test, all three must be yes: (1) could a viewer who watched the whole video say the title was accurate; (2) is every number in the title shown in the video; (3) does the thumbnail show an event that occurs in the video. If any is no, rewrite the title, not the test.

## 4. Thumbnail brief

Fill every field:

- **Focal subject**: one thing, readable when the image is about 168 by 94 pixels (the size of a small suggested-video tile).
- **Text**: at most 4 words, large, high contrast, does not repeat the title word for word, not placed in the bottom-right corner where the duration badge sits.
- **Emotion or state**: one, and it must match the video.
- **Background**: simple, one dominant colour that differs from the subject.
- **Proof element**: an object, screen or before/after that actually appears in the video.
- **Do not**: fake arrows at nothing, fake before/after, other people's faces or logos without permission.
- **Spec**: 16:9, 1280 by 720 pixels recommended, under 2 MB, JPG or PNG.
- **Alt option**: a second concept with a different focal subject, so the creator can compare.

## 5. Disclosure details

- Spoken: before the first sponsored mention, in plain words ("This video is sponsored by X").
- On screen: a visible "Sponsored" or "Ad" label during the segment.
- Description: first 150 characters, plain words; affiliate lines separate.
- Platform setting: the paid-promotion checkbox when uploading. It adds a viewer-visible label and does not replace the spoken and written disclosure.
- Gifted product or free trip counts as a material connection even with no payment.
- Law differs by country; the creator must check local rules. The validator treats a sponsored video as failing unless description wording, script wording and the toggle are all present.

## 6. Platform limits and sources

Limits used by the validator: title 100 characters; description 5,000 characters; tags 500 characters in total; chapters need a first timestamp of 0:00, at least 3 timestamps in increasing order, and at least 10 seconds each; thumbnail under 2 MB. The figures above are written from the author's knowledge; the source pages below were not fetched when this file was written, so confirm against them before relying on a limit.

- Video chapters: https://support.google.com/youtube/answer/9884579
- Paid product placements and the paid-promotion setting: https://support.google.com/youtube/answer/154235
- Thumbnails: https://support.google.com/youtube/answer/72431
- Endorsement disclosures guidance for influencers (US): https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers
