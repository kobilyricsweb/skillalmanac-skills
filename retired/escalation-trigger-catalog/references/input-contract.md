Required inputs are the escalation policy, measurable thresholds, named destinations, timing rules, evidence requirements, and supplied boundary examples. Include units, comparison operators, observation windows, repetition counts, and any exception or override clauses. If a policy uses vague terms such as serious or promptly without definitions, mark them unresolved. Missing destination or timing does not permit invention.

Output fields are triggers, example_evaluations, policy_gaps, outside_scope, and verification_report. Each trigger contains trigger_identifier, observable_condition, threshold, evidence, destination, timing, non_trigger_boundary, source_trace, and policy_gap. Evaluate examples literally and preserve one-way logic: an example that does not trigger does not establish every condition that would also fail.

The verification report contains one check for every trigger field and every controlling comparison operator, measurement window, repetition count, and supplied boundary. Each check names its subject, assigns preserved, unresolved, or conflicting status, cites the supplied source, and explains any issue. Report unresolved or conflicting checks in the report’s issues list; do not convert their uncertainty into a successful verification.

Do not add severity scales, external standards, diagnosis, or operational execution.
