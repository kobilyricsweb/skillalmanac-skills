# Worked Example

Synthetic example only.

Input records:

- A: name=`North Star`, code=`X7`
- B: name=`North Star`, code=`X7`
- C: name=` north star `, code=`X7`
- D: name=`North Star`, code=`Y9`

Rule: compare `name` and `code`; exact equality first; then trim and lowercase `name` only. No candidate threshold.

Expected artifact:

- Exact duplicate group: A, B. Both fields are exactly equal.
- Normalized match: C matches A/B under the stated name normalization, but original spacing and casing are preserved.
- Non-match under evaluated exact/normalized rules: D differs on code. Candidate assessment is not performed because no optional candidate rule was supplied; this does not make the exact/normalized result unresolved.
- Boundary: no merge, deletion, identity claim, or canonical winner is selected.

The report includes the rule used, original values, transformed name values, and the code conflict.
