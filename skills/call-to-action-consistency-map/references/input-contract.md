Required fields:

- asset_copy: each supplied asset’s surrounding message and exact current CTA;
- audience_stage_rules: allowed CTA transitions for each audience state;
- approved_ctas: approved wording and any scope or channel limits;
- destination_descriptions: factual descriptions of each linked destination;
- prohibited_transitions: disallowed stage or destination movements.

If a field is missing, create a partial map and identify the unresolved comparison. Output must include one row per asset, exact current CTA, audience state, the promise implied by that CTA, supplied destination description, stage result, destination result, mismatch explanation, and a proposed approved CTA where available.

Evaluate stage fit against stage rules, prohibited transitions, and approval scope. Evaluate destination fit only by comparing the supplied destination description with the current CTA’s implied promise. Separately record whether the current CTA or destination conflicts with the surrounding asset message. A destination may therefore fit the current CTA while the CTA remains prohibited for the audience stage or inconsistent with the asset message.

If proposing replacement wording, state whether the existing destination supports that replacement’s promise; if not, preserve the destination dependency. Use factual destination descriptions rather than names. Do not infer approval, destination capability, implementation status, or performance. Recommendations are proposals only.
