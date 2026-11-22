Required input fields:
- labeled validation rules;
- field or object scope for each rule;
- source ID for each rule;
- limits, predicates, units, and boundary wording;
- explicit precedence, exception, or applicability clauses, when present.

If scope, units, boundaries, or applicability are missing, identify the gap and mark affected comparisons undecidable when that missing evidence prevents determining the relationship itself. Missing precedence alone does not prevent classifying compatibility, redundancy, or contradiction; it prevents selecting a governing rule and leaves a genuine conflict unresolved. If one statement supplies purported precedence while another states that no precedence exists, preserve both as evidence, report the conflict between them, and leave governance unresolved unless the input identifies which statement controls. If rules conflict, retain every source and do not choose a winner. Compare only rules whose supplied scopes overlap or whose relationship is explicitly stated.

The output must include a field-level conflict map with source IDs, rule text or normalized constraint, scope intersection, classification, precedence evidence, and resolution-needed status. It must also identify unresolved questions and assumptions. The artifact analyzes operational compatibility; it does not create policy, implement validators, or treat silence as permission to relax or tighten a rule.
