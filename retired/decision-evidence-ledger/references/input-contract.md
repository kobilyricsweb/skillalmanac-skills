# Input contract

## Required

- Supplied decision notes, transcript excerpt, or written record.
- Any supplied participant, authority, time, status, and evidence information.
- Optional source labels or anchors.

## Handling gaps

Preserve missing facts as `not stated` or `not supplied`. Keep proposals, decisions, and other assertions as separate entries. Record a conflict only when supplied accounts are incompatible about the same status, decision, approval, or governing choice; a proposal that differs from a later decision is not automatically a conflict. Do not select a winner between genuinely conflicting accounts. Reported approval is not an authorized final decision unless the supplied record establishes scope-specific authority.

## Deliverable

Return schema-conforming JSON containing entries; typed relations with target ID, relation, and basis; conflicts with ID, related entry IDs, dimension, reason, and source references; and open questions with ID, text, source reference, and related IDs. Use `classification_basis`, never a confidence score.

Example: “Maya proposed CSV. Omar approved PDF.” Record the two statements separately. Their differing options do not alone create a conflict. PDF is final only if Omar's relevant authority is supplied; otherwise its status is reported approval with finality unresolved.
