# business-plan-outline

## One line

Writes a one-page business plan outline from the numbers a founder supplies, tags every figure as GIVEN or ASSUMPTION, and names the five assumptions that move the outcome most, each with a test.

## What it does

The skill takes a short intake: the problem, the customer, the offer and its unit price, the sales channel, the revenue model, the cost lines and the start month. It checks whether the critical items are present. If they are, it writes the plan in a fixed eight-section layout. Every number carries a tag, so a reader can see which figures came from the founder as known facts and which are estimates.

The arithmetic is fixed by the procedure. Contribution per unit is price minus variable cost. Break-even units per month is fixed cost divided by contribution, rounded up. The milestone table covers months 1, 3, 6 and 12. The assumption table ranks the estimates by how much month-12 profit moves when each one shifts 20 percent in either direction.

The skill declines to forecast revenue when no unit price was given. It stops and asks a numbered question list when a critical item is missing. It does not estimate a success probability, a funding amount or a valuation.

## When to use

- A founder has a product, service or local business idea and wants a one-page outline that separates known prices from guesses.
- A planning session needs to know which two or three estimates deserve testing before money is spent.
- The founder already has unit prices and rough volumes and wants them laid out with break-even and a 12-month ramp.

## When not to use

- A full financial model with multiple scenarios, depreciation schedules or tax lines.
- An investor deck or a funding request that needs market-size claims.
- A request for revenue with no price input. The skill refuses that forecast.
- Legal, tax or regulatory questions. The skill declines those parts.

## Requirements

No scripts, no network access and no installed packages. Any text-capable agent that can follow a numbered procedure and write markdown tables can run it. The user supplies the intake facts in chat.

## Example

The example uses a mobile bike repair idea with given prices, a smoke-test input chosen by the author. Every figure below was recomputed in Python before inclusion.

# Business plan outline: Mobile bike repair (working name Spoke Van)

Status: partial
Notes: start month not given; month 1 set as the first full month (ASSUMPTION).

## 1. Problem

Riders in one city district lose days waiting for a shop appointment, and many will not carry a bike to a shop at all. A van that comes to the rider solves the wait and the transport problem in one visit.

## 2. Customer

Adult commuters and weekend riders in the same district who own a bike they use at least weekly. Volume targets in section 7 are ASSUMPTION.

## 3. Offer

An on-site basic tune-up: brake and gear adjustment, tire check and chain cleaning, for $70 per visit (GIVEN). Parts cost $15 per visit (GIVEN).

## 4. Channel

Online booking through a scheduling app costing $40 per month (GIVEN), plus referrals from two local bike shops that do not offer on-site service.

## 5. Revenue model

| Line | Formula | Value | Tag |
|---|---|---|---|
| Unit price | given | 70 | GIVEN |
| Parts per unit | given | 15 | GIVEN |
| Labor per unit | 1 hour at estimated rate | 20 | ASSUMPTION |
| Units per month, month 12 | user target | 120 | ASSUMPTION |
| Revenue per month, month 12 | 120 x 70 | 8,400 | ASSUMPTION |

Contribution per unit: 70 - 15 - 20 = 35
Break-even units per month: 1,330 / 35 = 38
Flags: none

## 6. Cost lines

| Line | Amount per month | Tag |
|---|---|---|
| Van lease | 850 | ASSUMPTION (estimate; quote pending) |
| Insurance | 140 | ASSUMPTION |
| Booking software | 40 | GIVEN |
| Marketing | 300 | ASSUMPTION |
| Total | 1,330 | |

## 7. 12-month milestones

Units are the user's ramp target and are tagged ASSUMPTION.

| Month | Units | Revenue | Variable cost | Fixed cost | Profit |
|---|---|---|---|---|---|
| 1 | 30 | 2,100 | 1,050 | 1,330 | -280 |
| 3 | 60 | 4,200 | 2,100 | 1,330 | 770 |
| 6 | 90 | 6,300 | 3,150 | 1,330 | 1,820 |
| 12 | 120 | 8,400 | 4,200 | 1,330 | 2,870 |

## 8. Assumptions to test

Profit changes are measured on month-12 profit of 2,870.

| Rank | Assumption | Value | Profit change at -20% | Profit change at +20% | Test | Pass if |
|---|---|---|---|---|---|---|
| 1 | Units per month at month 12 | 120 | -840 | +840 | 14-day waitlist test | At least 30 units booked in 14 days (half of the month-3 target of 60, working value) |
| 2 | Labor cost per unit | 20 | +480 | -480 | Time five real visits | Average at or below 20 |
| 3 | Van lease per month | 850 | +170 | -170 | Two written lease quotes | Lower quote at or below 850 |
| 4 | Marketing per month | 300 | +60 | -60 | 14-day test capped at 300 | Cost per booking at or below 23 (one-third of unit price, working value) |
| 5 | Insurance per month | 140 | +28 | -28 | Two written liability quotes | Lower quote at or below 140 |

## Limits

- Volumes, labor and fixed costs are the founder's estimates. The plan is only as good as those inputs, and every one of them is tagged so the founder can replace it.
- Profit is shown before any owner pay, which the outline treats as outside the plan. A founder who draws a salary must add that line.
- Working values in the test column are not published standards. They are starting points for a decision, not benchmarks.
- The skill does not model tax, depreciation, seasonality or financing.
- A plan with partial status should be completed by answering the open questions before it is shared.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
