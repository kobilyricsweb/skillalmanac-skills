Required inputs:

- Old dependency release notes or documented baseline behavior.
- New dependency release notes, removals, renames, and behavior changes.
- Supplied usage references naming symbols, APIs, modules, or behaviors.
- Supported environment constraints.
- Project assumptions relevant to compatibility or migration.

If any input is missing, identify which impact dimensions cannot be assessed. Do not substitute general dependency knowledge. If a usage reference lacks a location or context, retain it as an ambiguous reference, but a direct naming of the changed symbol or behavior remains directly exposed under the exposure rule. If notes conflict, report both versions and avoid selecting one without an explicit project rule.

Output fields: documented changes, matched usage sites, exposure classification, required review, evidence, environment considerations, conflicts, unverified exposure, and a coverage limitation statement. A match indicates possible exposure only; absence from supplied references does not establish absence from the project.
