Required fields:

- testimonial_text: complete supplied testimonial, with speaker or source label if provided.
- permission_terms: exact written permission, including media, placement, duration, usage-count limits, attribution, and edit limits.
- attribution_preference: requested name, company, anonymous treatment, or unresolved preference.
- proposed_placement: named channel or asset, intended audience, and proposed use date when timing is needed to evaluate a duration limit.
- intended_excerpt: exact proposed excerpt, or an explicit request to review the full text.

For permission limited to a number of uses or issues, also supply designated issue dates, prior-use history, the proposed use's ordinal, or equivalent information establishing whether the proposed use remains within the permitted count. If that information is absent, keep applicability of the count-limited permission unresolved.

Optional fields may identify the requester, date, source location, designated uses, prior-use history, and the proposed use's ordinal. If a required field is missing, return a blocked readiness record naming the missing field; do not infer permission or scope. A duration stated only as a length, without an effective date or equivalent anchor and a proposed use date, does not establish that the use falls within the permitted period; keep that duration conclusion unresolved. Likewise, a count limit without supplied information locating the proposed use within that allowance does not establish coverage; keep that conclusion unresolved.

Before classifying an edit, search for the intended excerpt as an exact contiguous substring of testimonial_text and compare characters at those source positions. Capitalization is evaluated where the excerpt occurs in the source, not against the beginning of the complete testimonial or an independently capitalized sentence. Thus an excerpt beginning with a word that is lowercase at its source position remains exact and requires no capitalization disclosure. If no exact contiguous match exists, identify the actual difference before assessing permission.

Output must contain the readiness table, a blocker list, a concise decision summary, and a fact trace linking each conclusion to supplied text or terms. Keep exact words distinct from proposed edits. Treat conflicting inputs as unresolved conflicts. A ready designation requires explicit coverage of the proposed placement, attribution, excerpt, edits, applicable duration, and applicable usage-count limit. Missing or ambiguous permission blocks readiness; a conflict or supplied-information gap that prevents determining whether existing permission applies remains unresolved. Do not make legal, authenticity, typicality, truth, or performance determinations.
