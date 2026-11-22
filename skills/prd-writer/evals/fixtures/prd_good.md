# PRD: Saved carts

Status: Draft. Source: Slack threads and the Tuesday call notes. Author: Hana.

## Decisions needed
- How long is a saved cart kept: 30 days (Leo) or 90 days (Marta, for the loyalty team)? Decider: Hana.
- What does "for the holidays" mean as a date? Decider: CEO.

## Problem
Logged-in shoppers add items on mobile, come back on desktop and find an empty cart. Analytics shows 23% of mobile sessions add to the cart and leave without buying. Support receives about 40 tickets a month asking where the cart went, all from logged-in users.

## Users
Logged-in shoppers on web and the iOS app. Not guests in this version.

## Success metrics
- "Where did my cart go" tickets: baseline about 40 a month, target [needs data].
- Share of mobile add-to-cart sessions that leave without buying: baseline 23%, target 20% [proposed], checked one quarter after launch.

## Non-goals
- Guest carts: nothing to attach the cart to (Marta).
- Android app: it is being rewritten.
- Reminder emails: separate project (Hana).

## Requirements
- **R1 (Must)** A logged-in user's cart is stored on the account and appears on web and iOS. Accept: add an item on iOS, log in on web, the item is in the cart.
- **R2 (Must)** Carts changed on two devices are merged, keeping the higher quantity. Accept: set quantity 1 on web and 3 on iOS for one item, sync, the cart shows 3.
- **R3 (Must)** An item whose price changed or that is unavailable shows a notice on the item, not a popup. Accept: change a price, reopen the cart, the item shows "price changed".
- **R4 (Should)** A saved cart expires after the agreed period. Accept: see Decisions needed (period not decided).

## Risks and assumptions
- Risk: the holiday wish has no date, so scope cannot be checked against a deadline.
- [assumption] Guests do not need this, because no guest has written in.

## Open questions
- Is a saved cart kept 30 or 90 days? Positions: 30 (Leo) / 90 (Marta, loyalty team). Decider: Hana.
- What happens to an unavailable item at checkout: removed automatically or by the user? Decider: Dev.
