# Worked Example

Synthetic example; the flag and references are invented for this example.

Input: flag `new_player`, state `100% on`. Application reference `player.ts:42` selects the new player; configuration reference `PLAYER_MODE=new`; test reference `player.spec.ts:18` covers the new path. Policy says the owner must approve retirement. Rollback is restoring the prior release; no configuration rollback note is supplied.

Expected artifact: proposed planning order, not an order established by the supplied policy; approval and unresolved evidence gates remain visible.

1. Confirm owner approval under the supplied policy.
2. Request supplied reference-completeness evidence from the user/owner; only-reference status remains unknown. No repository inspection is performed.
3. Request user/owner-supplied configuration-activity evidence; activity remains unresolved. No live inspection is performed.
4. Update or remove the test only after the application dependency decision.
5. Plan flag cleanup after references are resolved.
6. Record release rollback as restoring the prior release; configuration rollback remains unknown.

Evidence gaps: universal reference completeness is not established; the 100% state does not prove the flag is removable; configuration activity is unresolved. No removal is performed or declared safe.
