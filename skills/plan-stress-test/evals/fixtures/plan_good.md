# Website relaunch

## Goal and success criteria
Launch the new site on 2026-05-12 with checkout conversion no worse than the old site (acceptance: 28-day conversion within 5% of baseline).

## Out of scope
Blog migration.

## Dependencies
- Payment provider sandbox keys (owner: Lena, due 2026-04-10)

## Rollback
If the error rate exceeds 2% in the first hour, switch DNS back to the old host (owner: Omar).

## Build
Owner: Ravi

- [ ] B1: Implement the checkout page (due 2026-04-20). Verify: all 14 checkout tests pass in CI
- [ ] B2: Integrate the checkout page once the payment provider sandbox keys arrive (owner: Lena, due 2026-04-22). Done when: a test payment settles in the sandbox

## Launch plan

| Step | Owner | Due | Verification | Depends on |
|---|---|---|---|---|
| Freeze content | Sofia | 2026-05-05 | editor shows zero drafts | B1 |
| Switch DNS | Omar | 2026-05-12 | smoke test passes on the new host | Freeze content |

## Risks and assumptions
- The payment provider approves the production account by 2026-05-01.
