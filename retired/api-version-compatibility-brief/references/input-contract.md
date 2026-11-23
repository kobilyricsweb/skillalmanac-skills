Required input fields:
- version_1: a labeled API specification;
- version_2: a labeled API specification;
- each specification’s paths and methods;
- request and response fields with documented types and requiredness;
- documented status codes and explicit behavior notes.

Optional inputs include source excerpts, version dates, and explicit rename or deprecation notes. If an inventory or behavior section is missing, say so and compare only the available evidence. If a specification contradicts itself, preserve the contradiction and mark affected comparisons uncertain.

The output must include an element-by-element comparison, classifications for unchanged, added, removed, renamed, changed, and behaviorally uncertain items where applicable, plus a concise unresolved-items section. Matching names are not sufficient for compatibility: type, requiredness, and semantics must align. The result is documentary analysis only; it does not test endpoints or establish migration readiness.
