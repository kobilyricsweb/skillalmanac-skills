Required inputs:

- complete draft, with stable passage markers if available;
- declared audience profile;
- known reader prerequisites;
- available resources and access;
- excluded assumptions or forbidden inferences.

The draft and profile must be sufficiently complete to compare stated expectations. If any required input is missing, identify the missing comparison and annotate only what remains evidenced; do not fill gaps from stereotypes or role labels.

Treat affirmative facts across the profile, prerequisites, and resource list as cumulative unless a supplied statement explicitly denies or limits another. Omission is not contradiction or exclusivity. For example, a profile that says readers are issued a printed handbook remains affirmative even if a separate resource list mentions only a browser PDF without saying that the PDF is the exclusive format. By contrast, “issued a printed workbook” and “the workbook is provided only as a PDF” directly conflict and require a conditional conclusion.

Return:

- annotations with passage, assumption type, evidence, consequence, and bounded clarification;
- unresolved conflicts or missing-input notes;
- a brief review-coverage note naming every relevant passage reviewed.

When any supplied prerequisite or resource supports a passage, do not invent uncertainty merely because another input omits the same support or unspecified interface details could vary. If compatibility is material, state explicitly in `coverage.reviewed_locations` that the passage requires no annotation and name the supporting fact. Do not rely on omission from the annotation list.

For explicitly conflicting resource formats, preserve both statements and prefer a format-neutral clarification that remains correct under either one. Do not choose a format or require the draft to name one unless the task requires that choice.

The output flags assumptions throughout prose, not procedural dependencies. It must distinguish explicit facts from inferences, avoid rewriting unless requested, and avoid treating absence of evidence as evidence of absence.
