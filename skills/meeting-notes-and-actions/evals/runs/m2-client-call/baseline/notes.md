# Northgate Hosting / Pellow Retail - Client Call Summary

**Date:** 12 November 2026
**Northgate:** Sam (account manager), Julia (support lead)
**Pellow Retail:** Samir (CTO), Ken (operations)

## Summary

Pellow Retail raised the 3 November outage, in which their checkout was down for 4 hours 10 minutes. Julia said the primary database node failed and traffic did not move to the standby as designed; the cause is still being confirmed and she declined to speculate on whether failover triggered. Samir pointed out that last month's uptime was 99.2% against a contractual 99.9%, and Sam acknowledged the SLA was missed. Pellow also said they could not reach anyone at Northgate for about 40 minutes during the outage. The affected-store count was corrected from 14 to **17** (three more reported the next morning).

## Who owes what

### Northgate owes Pellow Retail

| Action | Owner | Due |
|--------|-------|-----|
| Send the dedicated escalation phone number | Julia | Today (12 Nov) |
| Send the full root-cause report (why failover did not work) | Julia | Monday 16 Nov |
| Answer on the service credit, after taking it to finance | Sam | End of next week (Fri 20 Nov) |
| Send calendar invites for twice-weekly check-ins (replacing the weekly one) for the next month | Sam (Julia is out Thu/Fri) | Not stated; before the new cadence starts |
| Raise the premium-tier request internally | Sam | Not stated; no promised outcome or date |

### Pellow Retail owes Northgate

| Action | Owner | Due |
|--------|-------|-----|
| Send the list of the 17 affected stores | Ken | Tomorrow (Fri 13 Nov) |

## Agreed

- Weekly check-in becomes **twice weekly for the next month**, until Pellow is comfortable again.
- Northgate will set up a dedicated escalation line for Pellow.
- Northgate acknowledges the missed SLA (99.2% vs 99.9%).

## Requested but NOT committed

- **Service credit of 25% of the monthly fee.** Sam did not commit to a figure; he will take it to finance and respond. Samir expects "an answer, not another meeting."
- **Free upgrade to the premium tier for the rest of the contract.** Sam said it is above his level; he will raise it but made no promises.
- **Read access to Northgate's status page API.** Julia said "possibly" and will think about what is involved. No commitment and no date.

## Open questions

- Why the failover did not trigger or complete (root-cause report pending).
- Exact start date and duration of the twice-weekly check-ins.
- The 40-minute inability to reach anyone was addressed only through the escalation line; no other follow-up was discussed.
