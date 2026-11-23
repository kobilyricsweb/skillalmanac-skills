# Worked example

Input:

Legend: a cell marker applies only to that cell. R1C1 contains `Standard*`; R1C2 contains `Included`. Definition `*`: `delivery excluded`.

Supported artifact:

Scope map:

- R1C1 — value `Standard`; marker `*`; definition `*` (“delivery excluded”); authorized scope: R1C1 only; basis: explicit cell-only legend.
- R1C2 — value `Included`; marker: none; supplied qualifier: none; authorized scope: unresolved only as to any unsupplied qualifier, with no exclusion inferred.

Orphan markers: none.

Unbound definitions: none.

Unresolved scopes: no broader row, column, or table inheritance was supplied. The exclusion is not mapped to R1C2 or to the table generally.

Boundary note: the map records where the qualifier applies; it does not establish whether delivery was actually excluded, whether “Included” is accurate, or what the table means outside the supplied legend and definitions.
