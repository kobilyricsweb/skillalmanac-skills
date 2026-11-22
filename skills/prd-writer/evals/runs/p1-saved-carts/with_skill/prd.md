# PRD: Saved carts across devices

Status: Draft. Source: Slack (#product-ideas, #eng-web) and the Tuesday call notes, collected by Hana. Author: not stated in the notes.

## Decisions needed
1. How long is a saved cart kept: 30 days (Leo, support) or 90 days (loyalty team, relayed by Marta)? Nobody decided on the call. Decider: not named in the notes; needs a named owner (suggest Hana as PM to escalate).
2. Are reminder emails for saved carts in this version? Loyalty team says yes, Hana says no (separate project). Decider: not named in the notes.
3. What does "for the holidays" (CEO) mean as a date, and is it compatible with web plus iOS scope? No date is in the notes. Decider: CEO with Marta.
4. What exactly happens to an item whose price changed or that is out of stock when the shopper returns? Marta says this must be decided; Dev proposed a notice. Decider: Hana with Marta.

## Problem
Carts live in the browser session today (Marta), so a cart does not follow a shopper to another device. Analytics shows 23% of mobile sessions add something to the cart and leave without buying, and many of those shoppers come back on desktop to an empty cart (Hana). Support receives about 40 tickets a month that amount to "where did my cart go"; all come from logged-in users, since guests do not write in (Leo). Evidence is analytics and a support ticket count; no purchase or revenue figure is in the notes.

## Users
- Logged-in shoppers who start on one device and continue on another. They are the only group in this version.
- Not for this version: guest (not logged-in) shoppers, and Android app users.

## Success metrics
- Mobile sessions that add to cart and leave without buying: baseline 23% (analytics, per Hana), target [needs data], measured by the same analytics report.
- Support tickets of the "where did my cart go" type: baseline about 40 a month (Leo), target [needs data], measured by the support ticket count.
- Targets [needs data]: nobody on the call named a number to hit (Hana's notes). Targets must be set by the team before launch; see Open questions.

## Non-goals
- Guest carts. Marta: there is nothing to attach a guest cart to, so guest carts cannot be in the first version.
- Android app. The app is being rewritten, so it is skipped for now (Marta).
- Reminder emails: not listed as a non-goal or a requirement because the notes disagree; see Open questions.

## Requirements
- **R1 (Must)** A logged-in shopper's cart is saved to their account. Accept: log in on web, add an item, log out, log in again on another browser; the item is in the cart.
- **R2 (Must)** The saved cart appears on any supported device after login. Accept: add an item on the iOS app, log in on web; the same item is in the cart.
- **R3 (Must)** The saved cart works on web and in the iOS app. Accept: run the checks of R1 and R2 on both platforms; all pass.
- **R4 (Must)** When the same account adds items on two devices, the carts merge, and for an item present on both the higher quantity is kept. Accept: add item A with quantity 2 on one device and quantity 3 on another; after login on either device the cart shows item A with quantity 3 and no duplicate line.
- **R5 (Must)** A saved cart is kept for a fixed retention period and then removed. The length of the period is not decided (see Open questions). Accept: see Open questions (30 or 90 days); once decided, a cart older than the period is gone on login.
- **R6 (Should)** [proposed, Dev's suggestion, not agreed] When a saved item has a changed price or is out of stock, a small notice on the item says "price changed" or "no longer available"; no popup. Accept: change an item's price after saving; on return the item row shows the notice and no popup opens.
- **R7 (Should)** A guest shopper who logs in keeps the items they added as a guest in the current session. Accept: see Open questions (not discussed in the notes; included only to force a decision).

## Risks and assumptions
- Risk: the CEO's holiday expectation has no date in the notes and may not match the scope; see Decisions needed.
- Risk: the retention conflict (30 vs 90 days) also decides whether the loyalty team's reminder emails can work; leaving it open can block both.
- Risk: the 40 tickets a month come only from logged-in users, so the ticket baseline excludes guests, who are out of scope anyway.
- [assumption] The 23% figure is the right baseline for "returns on desktop to an empty cart"; the notes say "a lot" of them come back but give no number.

## Open questions
- Retention: 30 days or 90 days? Positions: 30, because after that people do not remember the cart (Leo) / 90, because the loyalty team asked for it (Marta, relaying). Decider: not named in the notes.
- Are reminder emails in the first version? Positions: yes, the loyalty team wants them / no, separate project (Hana). Decider: not named in the notes.
- Price changed or out of stock on return: is Dev's inline notice the agreed behaviour, and is the item kept in the cart or removed? Decider: Hana with Marta.
- What number do we want to hit for the cart-leave rate and for support tickets? Nobody set one. Decider: Hana.
- What date is "for the holidays"? Decider: CEO.
- Does R7 belong in this version? The notes only say guest carts cannot be in version 1. Decider: Marta.
