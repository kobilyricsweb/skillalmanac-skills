Required inputs:

- Cache key patterns and the entity or relationship each pattern represents.
- Read paths tied to one or more key patterns.
- Mutation events and the entities they change.
- Invalidation rules, including timing or ordering where documented.
- Stated staleness allowances and their scope.

If a relationship between a mutation and key is absent, mark it unresolved rather than inferring one. If timing is absent, report invalidation timing as unspecified. If staleness tolerance is absent, do not assume zero or eventual consistency. Conflicting rules remain visible as conflicts.

Output fields: scenario table, affected keys, readers, invalidation timing, allowed staleness, evidence, unresolved relationships, conflicts, and verification statement. The artifact is a specification aid, not proof of runtime cache behavior or a substitute for incident procedures.
