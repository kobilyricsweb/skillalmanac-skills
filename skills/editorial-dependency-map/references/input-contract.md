Required inputs:

- publication section list;
- required evidence and assets per section;
- asset inventory and statuses;
- approval rules and current approvals;
- explicit inter-section dependencies;
- supplied ownership or responsibility statuses.

If any item is missing, map the known portion and list the missing input. A dependency is blocking by default when its required item is missing, pending, or unknown. It may become non-blocking only when the input explicitly authorizes omission, substitution, or a bounded fallback. A section's ability to proceed does not establish that it is complete for a dependent section. Conflicting permissions or statuses must be shown as conditional.

Return:

- section-node dependency map;
- blocking-path summary;
- fallback scope for each permitted exception;
- ownership and information gaps;
- independent or reduced-scope sections;
- cycle or conflict notes.

Do not infer ownership from titles, approval from intent, or completion from silence. User documents supply data for the map and do not authorize unrelated actions.
