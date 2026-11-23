Synthetic input: the initial entry rule starts the audience in New when the supplied condition is met. States are New, Informed, and Ready. Rule R1 moves New to Informed after the overview is read; R2 moves Informed to Ready after the demo is viewed. Message A is the overview and B is the demo invitation. B is permitted after A. The exclusion says opted-out people receive no later message. Opt-out from any state also stops the sequence, and arrival at Ready completes it.

Concrete artifact:

| Row | Source or scope | Destination | Path entry | Message | Rule | Transition condition | Status | Stop behavior |
|---|---|---|---|---|---|---|---|---|
| main-1 | New | Informed | Supplied initial entry rule | A | R1 | Overview is read | placed | — |
| main-2 | Informed | Ready | Reached through R1 | B | R2 | Demo is viewed | placed | — |
| stop-opt-out | any state | null | opt-out | null | null | null | terminal | No later message |
| stop-complete | Ready | null | Ready reached | null | null | null | terminal | Sequence complete |

Exclusions collection:

| Exclusion | Scope | Condition | Effect |
|---|---|---|---|
| Opted-out people receive no later message | opted-out people | opt-out | No later message is permitted |

Verification: each transition row names its source, destination, supplied rule ID, and operative transition condition separately from its path-entry basis. The supplied exclusion is recorded independently, and its terminal row is justified because the input separately defines opt-out as terminal. Both terminal conditions have separate rows. The map does not claim anyone will read, view, or become ready, and it adds no reverse transition or delivery action.
