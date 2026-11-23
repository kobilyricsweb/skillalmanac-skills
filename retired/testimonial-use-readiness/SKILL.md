---
name: testimonial-use-readiness
description: "Use when reviewing supplied testimonial material for attribution, permission, excerpt scope, edits, duration, and placement readiness. Do not use for conducting interviews, eliciting new testimonials, designing a case-study interview, authenticating claims, assessing legal validity, or predicting campaign performance."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.7"
  network: none
---

Review the supplied testimonial text, permission terms, attribution preference, placement, intended excerpt, and timing. Preserve the complete source wording separately from the proposed excerpt.

First locate the intended excerpt as a contiguous exact substring of the source testimonial. Compare characters at their source positions, including capitalization and punctuation. Do not compare the excerpt’s first character with the testimonial’s sentence-initial character or apply sentence-start capitalization. If the exact excerpt occurs contiguously, its original lowercase initial is not an edit. Only after this check assess omissions, removed qualifiers, additions, reordered text, or disclosed edits.

Compare permission scope with placement, audience, attribution, excerpt form, edits, duration, and any usage-count limit. A bounded duration covers a proposed use only when supplied effective dates or an equivalent anchor establish that the use falls within the permitted period. A count-limited permission covers a proposed use only when designated uses, prior-use history, or equivalent supplied information establishes that the proposed use remains within the allowance. Mark a use `ready` only when supplied terms cover every proposed element and no material conflict remains. Otherwise use `blocked` or `unresolved` and name the smallest gap.

Classify an absent required proposal field—such as `intended_excerpt`, attribution, placement, or `permission_terms`—as `blocked` because the proposed use is incomplete. Classify missing contextual information needed only to determine whether supplied duration- or count-limited permission applies as `unresolved`, including a missing effective-date anchor, proposed use date, designated uses, prior-use history, or proposed-use ordinal.

For every blocked use, state each precise permission needed in both the blocker list and decision summary. Keep distinct gaps separate—for example, public-homepage permission and permission to use a shortened excerpt currently authorized only in full. Never substitute a vague request for broader permission.

Do not infer consent, authenticity, typicality, truth, broader rights, dates, usage history, or performance. Trace each conclusion to supplied text or terms, and keep publication, rewriting, and legal assessment outside scope.

Return JSON matching the [output schema](references/output-schema.json), following the [input contract](references/input-contract.md); the [worked example](references/worked-example.md) is illustrative only.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
