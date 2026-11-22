---
name: travel-planner
description: Builds a realistic trip itinerary with pacing limits by trip style, transit buffers, a budget table, a document checklist and a to-verify list for every hour, price and visa fact, then checks the itinerary file with a script that finds overlaps, overloaded days, missing buffers, unverified facts and budget totals. Use when the user asks to plan a trip, build or fix an itinerary, plan a weekend or a week in a city, budget a holiday, or check if a plan is too packed. Do not use for booking, live flight or hotel prices, visa legal advice, or route navigation.
license: Apache-2.0
compatibility: The checker needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the limits in step 5 by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Travel planner

Produce an itinerary the traveller can actually follow, and never state a fact you have not been shown. Opening hours, prices, visa rules, schedules and entry requirements change and differ by nationality and date. You do not know them for this trip. Write them as claims to verify, with the place to check.

## Verify-before-booking rule

Every hours, price, visa, booking-window or transport-time fact goes into the itinerary as `status: "unverified"` unless the user pasted it, or you read it from a page this session and can give the URL and date. Never write "open 9-17", "costs 20 EUR" or "no visa needed" as plain text in the plan. Write "Castle: hours unverified, check the official site" and put the claim in the to-verify list. A planned time slot is a proposal, not a promise that the place is open. Say once, near the top of the answer, that nothing in the plan is booked or confirmed.

## Workflow

```
- [ ] 1 Collect trip facts (ask only what is missing)
- [ ] 2 Choose the pace
- [ ] 3 Draft days as itinerary JSON
- [ ] 4 Add budget lines and documents
- [ ] 5 Run the checker and fix errors
- [ ] 6 Report
```

1. **Collect.** Needed: dates or length, start and end city, number of travellers, home-country passports (for documents), total budget with currency, interests, mobility limits, must-sees, trip style. If dates are missing, plan "day 1..n" and put real dates in once known. Ask at most 4 questions; assume the rest and list the assumptions.
2. **Pace.** Pick the style from what the user says, default `balanced`. Ask no extra question for it.

   | Style | Max activities per day | Max scheduled non-meal hours | Typical user words |
   |---|---|---|---|
   | relaxed | 2 | 6 | slow, with kids, retired, rest days, no rush |
   | balanced | 3 | 8 | default, first visit, mixed ages |
   | packed | 4 | 10 | short trip, see everything, fit, repeat visitor |

   A travel day (arrival, departure, a long transfer) loses one activity slot. Meals and transit blocks do not count as activities. After 5 consecutive full days, schedule one light day. Do not place a big activity within 2 hours after landing or within 3 hours before a departure.
3. **Draft** one JSON file following the contract below. Group each day by area so there is no zig-zag. Put the fixed-time item (tour, ticket slot, reservation) first, then fit the flexible ones around it. Give every day one meal block.
4. **Budget and documents.** Put every paid item's cost on the item (`cost` for the whole party or `cost_per_person`) with a `category`. Leave 10% of the budget unplanned; the checker warns below that. Fill `trip.documents` from [references/documents-and-verification.md](references/documents-and-verification.md); read only the part that matches the trip type (international, driving, with children, cruise or rail pass) and the table of where to verify each fact kind.
5. **Check.** Run `python scripts/itinerary_check.py trip.json`. Read the JSON, fix every `error`, then decide on each `warning`. Run the script, do not edit it, and do not change a limit to make a check pass. Re-run until `"ok": true`. Without Python, check by hand: no two blocks overlap, activities per day are within the table, between two places there is at least 15 minutes inside one area and 30 across areas plus the travel time, every fact has a status, and the summed item costs stay within `trip.budget_total`. The script compares item costs only; a `trip.budget` object with per-category lines is ignored, so check any such lines by hand.
6. **Report** in the fixed format below.

## Itinerary file contract

Copy [assets/itinerary_template.json](assets/itinerary_template.json) and fill it in. Times are 24-hour `HH:MM`; a block cannot cross midnight (split it). For the tuning numbers behind the checks (buffers, caps, stale window) read [references/pacing-and-budget.md](references/pacing-and-budget.md) only if the user disputes a finding.

- `trip`: `style` (relaxed, balanced, packed), `currency` (one only), `travelers` (integer), optional `budget_total`, `facts` (trip-wide facts such as visa), `documents` (`name`, `status` have, todo or unverified).
- `days[]`: `date` (YYYY-MM-DD), optional `travel_day` true, `items[]`.
- `items[]`: `id`, `title`, `kind` (activity, meal, transit, lodging, other), `start`, `end` (lodging may omit both), `location`, optional `area` (same area string means same neighbourhood), optional `travel_from_previous_min` and `arrive_early_min`, `cost` or `cost_per_person`, `category` (lodging, food, activities, transport, other), `facts[]`.
- `facts[]`: `claim`, `kind` (hours, price, visa, booking, transport, other), `status` (verified or unverified); a verified fact needs `source` and `checked_on`.

The checker prints one JSON object: `ok`, `summary` (days, items, activities, errors, warnings, facts_to_verify), `findings[]` (`severity`, `code`, `day`, `item`, `message`), `to_verify[]`, and `budget` (by category, by day, total, budget_total, remaining). Exit 0 when no errors, 1 when errors, 2 when the file cannot be read.

Finding codes: `overlap`, `pacing_limit`, `long_day`, `no_meal_block`, `missing_transit_buffer`, `unverified_fact`, `verified_without_source`, `stale_check` (verified over 30 days before the trip), `hours_not_listed`, `price_not_listed`, `over_budget`, `thin_contingency`, `missing_cost`, `mixed_currency`, `missing_location` (warning), `schema`.

A timed item without `location` is a defect, not a skip: it gets a `missing_location` warning and the buffer check still runs, using `area` as the place identity (same area means 15 minutes, different area means 30) and, with neither field, assuming a different place. Two overlapping blocks get only the `overlap` error, no buffer message.

## Fixed report format

1. One line: dates, style, travellers, budget. "Nothing here is booked or confirmed."
2. Day-by-day table: time, activity, place, status of hours (unverified, or verified with date).
3. Budget table: category, planned, share of total; remaining and contingency.
4. Document checklist with status.
5. To-verify list, grouped by what to check and where (official site of the venue, the issuing government's entry page, the carrier). Copy it from `to_verify`.
6. Assumptions made, and the checker result (errors fixed, warnings left and why).

## Limits

The script checks internal consistency only; it cannot know that a museum is closed on Monday, that a transfer takes 50 minutes, or that a visa is required. Travel times you enter are your estimates unless a source is given. It handles one currency and no overnight blocks. It does not book, search live prices or read maps. Visa and health rules are not legal or medical advice; send the user to the official source. Passport numbers, card numbers and other identifiers are out of scope: never ask for them.
