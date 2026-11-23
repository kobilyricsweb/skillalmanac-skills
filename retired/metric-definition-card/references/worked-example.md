# Worked Example

Synthetic example only.

Input: metric name `activation rate`. Note: “percentage of new accounts that activate within 14 days.” No activation event, timezone, exclusion, freshness, or zero-denominator policy is supplied.

Expected artifact:

- Formula: 100 × (activated new accounts within 14 days / new accounts), expressed as a percentage; activation-event and population gaps below remain unresolved.
- Class: percentage, as explicitly stated by the supplied note.
- Numerator: unresolved; “activate” needs an event definition.
- Denominator: new accounts, with eligibility boundary unresolved.
- Population: new accounts; cohort start definition unresolved.
- Window: 14 days; timezone and inclusive boundary unresolved.
- Exclusions: not supplied.
- Freshness: not supplied.
- Missing/zero policy: unresolved.
- Questions: What event constitutes activation? Which account creation timestamp starts the window? What happens when the denominator is zero?

No activation rate is calculated and no product recommendation is made.
