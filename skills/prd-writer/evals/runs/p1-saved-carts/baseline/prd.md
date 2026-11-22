# PRD: Saved Carts (cross-device cart for logged-in users)

Status: Draft v1 | Date: 2026-11-20 | Sources: #product-ideas, #eng-web, Tuesday call notes

## 1. Problem
Carts live in the browser session, so they do not follow the user. Evidence:
- 23% of mobile sessions add an item to the cart and leave without buying (analytics). Many return on desktop and find the cart empty.
- Support gets about 40 tickets/month of the "where did my cart go" type, all from logged-in users.

## 2. Goal
A logged-in user's cart is saved to their account and appears on any device.

### Success metrics
**Not defined in the source notes. Needs an owner decision before build.** Candidates (no targets proposed, since nothing in the notes supports a number):
- "Where did my cart go" tickets (baseline about 40/month)
- Share of mobile cart-abandoners who later complete a purchase on any device (baseline: 23% of mobile sessions abandon)

## 3. Scope
### In scope (v1)
- Logged-in users only.
- Platforms: web and iOS app.
- Cart saved to the account and loaded on any signed-in device.
- Merge when the cart is changed on two devices: union of items, keeping the higher quantity per item (agreed on the call).
- Item-level notice when a returning user's item changed: "price changed" or "no longer available". Inline notice, not a popup (designer proposal; eng raised that these cases need a decision).

### Out of scope (v1)
- Guest carts. There is nothing to attach a cart to (eng).
- Android app (being rewritten; revisit after).
- Reminder emails for saved carts. The loyalty team wants them; the PM decided it is a separate project.

## 4. Requirements
| # | Requirement | Source |
|---|---|---|
| R1 | A logged-in user's cart persists to their account | Hana, Marta |
| R2 | Cart is available after login on web and iOS | Marta |
| R3 | Edits on two devices merge; per-item quantity = the higher of the two | Tuesday call |
| R4 | On return, an item whose price changed shows an inline "price changed" notice | Dev |
| R5 | On return, an unavailable item shows an inline "no longer available" notice | Dev |
| R6 | Saved carts expire after N days (see open question 1) | Leo, Marta |

Not specified in the notes (to settle in design/eng): which price applies at checkout when it changed, whether an unavailable item stays in the cart or is removed, and how a guest cart built before login is handled. Flagged, not decided.

## 5. Open questions
1. **Retention: 30 or 90 days?** The support lead wants 30 (people forget); the loyalty team wants 90 (for reminder emails). Undecided. The 90-day driver depends on reminder emails, which are out of v1, which argues for 30 unless that changes. This is a recommendation, not a decision.
2. **Launch date.** The CEO wants it live "for the holidays". No date or eng estimate in the notes. Needs an estimate from Marta to see whether v1 fits.
3. **Success metric and target** (section 2).
4. **Behavior when price or stock changed** (section 4).

## 6. Risks
- Holiday deadline with no estimate.
- Guests are excluded, so users who browse logged out still lose their cart. Guests file no tickets today, so the ticket metric will not capture this.
