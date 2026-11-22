# Input Contract

Required:

- `items`: supplied item identifiers or labels.
- `categories`: category identifiers with definitions.
- `assignments`: existing item-to-category relationships.

Optional:

- `constraints`: exclusivity, incompatibility, required definition elements, or coverage rules.
- `review_scope`: selected items or categories.

Decision rules:

- No assignment means unassigned.
- A membership conflict requires an explicit incompatibility supplied either as a standalone constraint or as operative wording in a category definition.
- Definition wording such as “excludes paper badges” may establish a conflict when the supplied item description and assignments directly satisfy that exclusion. Cite the exact definition clause as the violated rule.
- Do not derive exclusivity from category labels, apparent semantic overlap, intuition, or an unattributed recommendation.
- Weak-definition findings require a stated standard or direct textual evidence.
- Self-reference is reported as a definition issue, not graph validation.
- Unknown authority and missing evidence remain unresolved.

Boundaries:

- Do not add assignments or categories.
- Do not validate parent graphs.
- Do not rank keywords or infer demand.
- Preserve supplied identifiers and wording.
