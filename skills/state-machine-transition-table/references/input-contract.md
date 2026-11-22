Required input fields:
- states: named states, with any supplied descriptions;
- events: event names and definitions;
- guards: conditions attached to events or transitions;
- effects: documented outcomes;
- optional source labels or note excerpts for traceability.

If a field is absent, do not invent it. State which input is missing and produce only the supported partial model. If names, guards, or effects conflict, preserve both versions and mark the affected row unresolved.

The output must contain a transition table with source state, event, guard, destination, effect, evidence, and status. It must also contain unresolved cases and explicit assumptions, if any. Unlisted combinations are unspecified unless the input explicitly supplies a default rule. “Unspecified” is distinct from “forbidden.” The artifact is an analysis of supplied prose, not code, a test result, or a system change request.
