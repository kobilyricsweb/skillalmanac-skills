Required fields: complete article text; declared audiences; task list; heading structure; and content that must remain together. Optional fields may include existing URLs, ownership, redirect conventions, localization constraints, and review responsibilities. If a required field is missing, identify it and provide only a bounded provisional map from supplied material; do not infer absent tasks or audiences.

Return exactly one JSON document with no surrounding or trailing prose. It must contain: proposed article units; boundary rationale; retained shared context; cross-link or repetition treatment; duplicate-risk notes; section-to-unit mapping; migration checklist; verification findings; and focused open decisions.

Assign every heading one consistent placement: a task unit, a retained shared location, or a decision needed. A heading represented in `shared_context` and mapped as `retained` must not also appear in any unit’s `retained_sections` or `moved_sections`. Unit section lists contain only sections assigned to that unit. Preserve headings and wording references sufficiently for reviewers to locate source material.

Treat “must remain together” as a hard constraint unless the input explicitly requests an exception. Evaluate duplication separately for shared context and procedural instructions. If an operational step from one task is repeated or restated in another unit—including scan, reconnect, restart, verification, or follow-on instructions—name that step and both affected units in `duplicate_risks`. If a canonical location plus cross-link avoids repetition, record that treatment without claiming duplication.

A proposal is not an executed migration. Supplied permissions do not authorize unrelated edits, publication, redirect changes, or content deletion.
