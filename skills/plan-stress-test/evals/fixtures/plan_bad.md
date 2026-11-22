# Billing database migration

## Goal
Move billing from the old Postgres host to the new managed cluster with under 5 minutes of write downtime.

## Steps

- [ ] A1: Freeze schema changes on the old host (@priya, due 2026-03-02)
  - Verify: no migration files merged after the freeze date
- [ ] A2: Build the new cluster after the network team opens the firewall ports (owner: Marcus, due 2026-03-04)
- [ ] A3: Copy data to the new cluster (owner: Priya, due 2026-03-03) depends on A2
- [ ] A4: Run the cutover rehearsal (@marcus)
- [ ] A5: Switch the application to the new cluster
  - Done when: error rate stays under 0.5% for 30 minutes
- [ ] A6: Update the runbooks (TBD)
- [x] A7: Order the new cluster (@priya, 2026-02-20)

## Risks
- The vendor may be slow.
