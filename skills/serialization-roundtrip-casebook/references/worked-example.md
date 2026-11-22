Synthetic input:

Type rule: nickname may be missing or empty. Missing nickname is omitted; empty nickname is preserved. Dates normalize to UTC. For timestamps, semantic equality means equality of represented instants rather than equality of source spelling or offset. Byte equality is not specified.

Concrete artifact:

| Case | Source | Serialized | Reconstructed | Semantic result |
|---|---|---|---|---|
| missing nickname | absent | field omitted | absent | equal |
| empty nickname | nickname="" | nickname="" | nickname="" | equal |
| date normalization | 2026-01-01T02:00+02:00 | normalized UTC date | 2026-01-01T00:00Z | equal because both represent the same instant |

The date transformation loses the original spelling and +02:00 offset even though it preserves the represented instant. Byte equality is unresolved for every case because no encoding, exact byte sequence, or complete canonical byte rule was supplied.

Verification statement: applying only the stated omission, preservation, UTC-normalization, and instant-equality rules produces the results above. No runtime serializer was executed, and no implementation change was made or proposed.
