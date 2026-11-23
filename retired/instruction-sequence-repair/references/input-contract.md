Required inputs:

- complete ordered instruction steps;
- explicit dependency statements;
- starting state;
- expected end state;
- immutable step text or a clear indication of what cannot change.

If a dependency, state, or immutable-text rule is missing, report the omission and repair only the supported portion. If dependencies conflict or form a cycle, preserve the conflict, identify affected steps, and do not present an unconditional complete order. Do not infer dependencies from ordinary practice.

Return:

- repaired ordered steps using unchanged immutable text;
- a move log with original position, new position, and supporting dependency;
- verification placement notes;
- unresolved dependency, state, or reachability issues.

The output repairs sequence order, not the content itself. All original actions must remain traceable. A verification checkpoint may be repositioned only when the input identifies its target action.
