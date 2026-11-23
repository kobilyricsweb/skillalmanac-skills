# Input Contract

Required:

- `metric_name`.
- `source_material`: notes, formulas, event definitions, schema references, or constraints.

Optional:

- `purpose`.
- `sample_values`: context only, never a result definition.
- `requested_format`: card or structured sections.

Decision rules:

- Preserve the supplied formula and decompose it into components.
- Population, window, timezone, exclusions, freshness, and zero policy must be stated or marked unresolved.
- Ambiguous business terms become clarification questions.
- Conflicting notes remain visible with provenance.
- No result is calculated.

Boundaries:

- Do not invent eligibility, date boundaries, exclusions, or denominator policy.
- Do not make causal, financial, or operational recommendations.
- Do not audit weighted-rate implementation.
- Do not treat sample values as a metric result.
