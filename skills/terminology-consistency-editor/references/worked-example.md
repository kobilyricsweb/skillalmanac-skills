# Worked Example

Synthetic example; terms and passage are invented for this illustration.

Input glossary:

- Concept: saved search configuration; preferred term: `saved search`; variant: `stored search`.
- Concept: search execution; preferred term: `run`; variant: `execute`.

Protected text: code identifiers and quotations.

Passage: “Create a stored search, then run it. The API field `stored_search_id` identifies the configuration. A reviewer said, ‘Execute the search only after approval.’”

Expected artifact:

Preferred-terms table: saved search → observed “stored search”; run → observed “execute” in quoted speech only.

Replacement list:

- First sentence, “stored search” → “saved search”; same configuration meaning.
- Quoted sentence: no change; quotation is protected.
- `stored_search_id`: no change; code identifier is protected, even though its name contains a glossary variant.

Unresolved distinctions: none. Verification report: one ordinary prose replacement is glossary-supported; quotation and identifier remain unchanged; no broader factual or style edit is proposed.

Scope/exclusions: editable prose in the supplied passage; quotations and code identifiers protected.

Candidate inventory: stored search in first sentence, run in first sentence, stored_search_id in code, Execute in protected quote.

|Concept|Preferred term|Observed variant|Scope|Glossary basis|
|---|---|---|---|---|
|saved search configuration|saved search|stored search|editable first sentence|explicit supplied concept/variant mapping|
|search execution|run|Execute in quoted speech|quote excluded from edits|explicit supplied mapping, protection overrides default replacement|
