Required inputs:

- Type rules for source and reconstructed values.
- Serialization format, field representation rules, and encoding when byte claims are requested.
- Omission and default behavior for missing values.
- Normalization rules, including precision, ordering, or timezone handling when stated.
- Representative synthetic values or explicitly requested cases.

If a rule is absent, mark the affected roundtrip property unknown. If a source value is missing, do not invent one. If a transformation is one-way, identify the lost information. Conflicting rules remain visible and prevent a definitive expected result.

Output fields: case identifier, source value, serialized form, reconstructed value, semantic equality result, byte equality result, information-loss assessment, ambiguity notes, and verification statement. Treat semantic and byte equality as separate claims. Byte equality remains unresolved unless exact bytes plus encoding or a complete canonicalization rule are supplied; a format name alone is insufficient.
