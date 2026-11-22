# Northgate Hosting / Pellow Retail call, 12 November 2026

Attendees: Sam, Julia (Northgate); Samir, Ken (Pellow Retail)

## Summary
Pellow Retail raised the 3 November outage that took checkout down for 4 hours and 10 minutes and affected 17 stores. Northgate acknowledged missing the SLA. Check-ins move to twice a week for the next month; the service credit and premium tier requests remain open.

## Decisions
- Weekly check-in becomes twice a week for the next month. (Proposed by Sam, accepted by Samir; 00:05:40-00:05:55)
- Northgate will set up a dedicated escalation line for Pellow Retail. (Julia agreed to Ken's request; 00:04:28)

## Action items
| Owner | Action | Due | Source |
|---|---|---|---|
| Julia | Send the full root-cause report on the database failover failure | 2026-11-16 ("by Monday") | Julia, 00:01:31 |
| Julia | Send Pellow Retail the number for the dedicated escalation line | 2026-11-12 ("today") | Julia, 00:04:28 |
| Sam | Take the 25% service credit request to finance and come back to Samir with an answer | end of next week | Sam, 00:03:24 |
| Ken | Send Northgate the list of affected stores | 2026-11-13 ("tomorrow") | Samir, 00:05:05; Ken, 00:05:12 |
| Sam | Send the invites for the twice-weekly check-ins | No date set | Sam, 00:06:09 |
| Sam | Raise the request to move Pellow Retail to the premium tier at no cost for the rest of the contract (no promises made) | No date set | Sam, 00:06:47; Samir, 00:07:02 |

## Open questions
- Did the failover trigger, and why did traffic not move to the standby? Julia said the root-cause report will answer this. (Ken asked; Julia)
- Will Northgate grant a service credit of 25% of the monthly fee? Sam could not commit a number on the call. (Samir asked; Sam, after finance)
- Will Pellow Retail be moved to the premium tier at no cost? Above Sam's level; no commitment. (Samir asked; Sam)
- Should Pellow Retail get read access to the status page API? Julia said she would think about what is involved. (Ken asked; Julia)

## Discussed, not decided
- None
