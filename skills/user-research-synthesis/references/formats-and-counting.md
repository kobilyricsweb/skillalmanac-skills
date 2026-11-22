## Contents

- Counting rules
- Splitting raw notes
- Starter codebook
- Worked grouping example
- Sources

## Counting rules

- Count **participants**, not notes or quotes. A theme's size is the number of distinct participants with a valid quote in it.
- A note is cited at most once per theme. A second quote from the same note adds no weight.
- A participant may appear in both `quotes` and `contradictions` of a theme (people hold mixed views). Count them on both sides; in the report say they are on both.
- The denominator `T` for "k of T" is the number of participants in the study, from the `participants` list when given, otherwise the distinct ids in the notes. Interviews where the topic never came up still count in `T`; if a theme concerns only a segment, state that segment as the denominator in the report and keep the file's `T` in the statement, for example "3 of 6 participants (all 3 admins)".
- Contradiction caps: one contradicting participant stops `high`; contradicting participants numbering at least half of the supporters force `low`.
- A signal is written down with the same ids but has no confidence and no entry in `themes.json`.

## Splitting raw notes

- One idea per note. "The app lost my photo and then support never replied" becomes two notes with the same participant.
- Keep the participant's words even when they are rambling; cut with `...` only inside quotes in the themes file, never in the notes.
- Mark as `kind: "observation"`: facial reactions, what the participant did on screen, the interviewer's inferences, and anything the participant did not say.
- Interviewer questions are not notes. If an answer depends on the question ("Did you find it slow?" "Yes"), write the note as the question context plus the answer, or leave it out: a leading question's yes is not evidence.
- Keep the same participant id across sessions, including follow-ups.

## Starter codebook

Start from the research question and keep it under 15 tags. A generic start for a product study: `onboarding`, `discovery`, `core-task`, `errors`, `speed`, `trust`, `pricing`, `support`, `workaround`, `comparison`, `request`. `workaround` (what people do instead) and `trust` are the tags most often under-used and most often useful. Replace any of these with words from the study.

## Worked grouping example

Six participants; tag `approval-delay` has 9 notes. Reading them: 5 participants describe waiting days (claim A), 3 describe not knowing who holds the report (claim B), one describes a rejected report (claim C). Result: A and B overlap in 3 participants but are different claims, so keep both as themes only if each clears 3 quotes and 3 participants; A does (5), B does (3); C is a signal. Merging A and B into "approvals are slow and opaque" is allowed only if every quote in the merged theme supports both halves; otherwise keep them apart. Then search the other participant's notes for approvals that went fast and add them as contradictions to A.

## Sources

Read for background and written in this file's own words; check them before relying on a figure.

- Affinity diagramming, as practised in UX research: https://www.nngroup.com/articles/affinity-diagram/
- Braun and Clarke, thematic analysis in psychology (2006): https://doi.org/10.1191/1478088706qp063oa
- Guest, Bunce and Johnson, how many interviews are enough (2006), the basis for treating small interview sets as able to show recurring themes but not their prevalence: https://doi.org/10.1177/1525822X05279903

The 3 quotes, 3 participants, 50%, 25% and 40% values are house working values, not taken from these sources.
