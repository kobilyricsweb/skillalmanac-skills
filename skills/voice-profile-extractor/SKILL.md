---
name: voice-profile-extractor
description: Builds a reusable voice profile from the user's own writing samples by measuring sentence length, paragraph length, contractions, person use, question and exclamation rates and favorite connectors, then writing a ten-line do and avoid profile with one before and after sample. Use when the user wants drafts in their own style, asks how their writing is built, or supplies three or more of their own writing samples. Do not use for imitating a named author, a living writer or any third party, for grading writing quality, or for drafting with no samples.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Voice Profile Extractor

Builds a 10-line voice profile from the user's own samples. Every count is done by hand from the text the user supplied. The profile rules come from the fixed bands in step 6. Shipped files: [LICENSE.txt](LICENSE.txt).

## Step 1. Intake check
Output: the Intake table (Sample, Words, Sentences, Paragraphs), filled in step 3.
- Samples must be the user's own writing. Label them S1, S2, S3 and so on in the order given.
- Minimum: 3 samples and 600 words in total after cleaning (step 2). Word counting follows step 3.
- If a minimum is missing, go to "Refuse / stop when" and return the question list.

## Step 2. Clean each sample
Output: one cleaned word count per sample, and a flag for every removal.
- Remove quoted replies, block quotes, code, link lists, email signatures, headings, tables and any passage the user attributes to someone else. Flag each removal as CLEANED.
- Replace phone numbers, account numbers and ID numbers with [redacted]. Flag as REDACTED.
- If quoted or pasted material is more than 30 percent of a sample's words, stop for that sample and ask the user to confirm authorship (see the refuse list).
- A cleaned sample under 100 words is dropped. Flag as DROPPED. Dropping one sample sets the status to partial.

## Step 3. Split and count units
Output: sentence and paragraph counts for each sample, used in the Intake table.
- Word: a whitespace-separated token that contains a letter or digit. Hyphenated words and contractions count as one word.
- Sentence: ends at . ! or ? followed by a space, line end or closing quote. Do not end a sentence at e.g., i.e., Mr., Dr., St., vs. or U.S. An ellipsis counts as one ending.
- Paragraph: a block of text between one or more blank lines.

## Step 4. Count the style markers
Output: the raw counts for every sample, in the Measurements table and the Connectors table.
- Contractions: tokens ending in n't, 're, 've, 'll, 'd or 'm, plus 's only after it, that, there, here, what, who, he, she or let. Curly apostrophes count the same as straight ones.
- First person: I, me, my, mine, myself, we, us, our, ours.
- Second person: you, your, yours, yourself.
- Questions: sentences ending in ?. Exclamations: sentences ending in !.
- Connectors: count only however, but, so, because, and, also, still, then, instead, though, yet. Report the five with the highest combined count. Ties are sorted alphabetically.
- Matching is case-insensitive. Write each count down before adding it to a total.

## Step 5. Compute the rates
Output: seven rates per sample and for the Combined column.
- Words per sentence = words / sentences, one decimal.
- Sentences per paragraph = sentences / paragraphs, one decimal.
- Contractions, first person and second person per 100 words = count / words x 100, one decimal.
- Questions and exclamations per 100 sentences = count / sentences x 100, whole number, round half up.
- The Combined column uses summed counts over summed totals. Do not average the sample rates.

## Step 6. Apply the bands and stability check
Output: a band label for each of the seven rates, and any UNSTABLE flags.

| Rate | Low band | Mid band | High band |
|------|----------|----------|-----------|
| Words per sentence | under 12 (short) | 12 to 20 (medium) | over 20 (long) |
| Sentences per paragraph | 1 to 3 (short) | 4 to 6 (medium) | 7 or more (long) |
| Contractions per 100 words | under 1.0 (formal) | 1.0 to 4.0 (mixed) | over 4.0 (conversational) |
| First person per 100 words | under 2.0 (low) | 2.0 to 6.0 (medium) | over 6.0 (high) |
| Second person per 100 words | under 1.0 (low) | 1.0 to 3.0 (medium) | over 3.0 (high) |
| Questions per 100 sentences | under 10 (rare) | 10 to 19 (occasional) | 20 or more (frequent) |
| Exclamations per 100 sentences | under 5 (rare) | 5 to 9 (occasional) | 10 or more (frequent) |

All bands are working values, not a published spec. Band tests use the rounded value shown in the table.

Stability: for each of the seven rates, spread = (highest sample rate - lowest sample rate) / Combined rate. If spread is above 0.50, flag UNSTABLE and name the rate. If the Combined rate is 0, skip the test.

Mixed-voice fallback: if more than 3 of the 7 rates are UNSTABLE, or fewer than 3 of the five candidate metrics in step 7 have a rate that is not UNSTABLE, set Status to `partial`. Write only lines 1 to 4 of the voice profile, with each UNSTABLE rate marked by appending [UNSTABLE] after its band clause. Skip lines 5 to 10 and step 8. Then ask the user whether the samples share one voice.

## Step 7. Write the voice profile
Output: exactly ten numbered lines under "Voice profile".
- Line 1: Sentence length: <band> (<n> words per sentence).
- Line 2: Paragraph length: <band> (<n> sentences per paragraph).
- Line 3: Contractions: <band> (<n> per 100 words); first person <band> (<n> per 100 words); second person <band> (<n> per 100 words).
- Line 4: Questions: <band> (<n> per 100 sentences); exclamations: <band> (<n> per 100 sentences); top connectors: <c1>, <c2>, <c3>.
- Lines 5 to 7: one Do rule for each of three chosen metrics, in the order chosen. Each line is "Do: " followed by the Do text.
- Lines 8 to 10: one Avoid rule for the same three metrics, in the same order. Each line is "Avoid: " followed by the Avoid text.

Choosing the three metrics: go through this order, Sentence length, Paragraph length, Contractions, First person, Questions. Take the first three whose band is not mid, in that order. If fewer than three are not mid, fill the gap with mid-band metrics in the same order. A rate flagged UNSTABLE is never chosen. Put the measured value in place of {n}.

| Metric and band | Do text | Avoid text |
|-----------------|---------|------------|
| Sentence, short | Keep sentences near {n} words. | sentences over 20 words. |
| Sentence, medium | Keep sentences near {n} words. | sentences over 25 words. |
| Sentence, long | Let sentences run to about {n} words when the idea needs room. | strings of fragments under 8 words. |
| Paragraph, short | End paragraphs after about {n} sentences. | paragraphs over 5 sentences. |
| Paragraph, medium | Write paragraphs of about {n} sentences. | paragraphs over 8 sentences. |
| Paragraph, long | Group about {n} sentences into each paragraph. | one-sentence paragraphs. |
| Contractions, formal | Write full forms such as do not and it is. | contractions such as don't and it's. |
| Contractions, mixed | Use contractions in about {n} of every 100 words. | contractions in consecutive sentences. |
| Contractions, conversational | Use contractions freely, about {n} per 100 words. | stiff full forms where a contraction fits. |
| First person, low | Keep the writer in the background, about {n} first-person words per 100. | opening paragraphs with I. |
| First person, medium | Keep first-person use near {n} words per 100. | shifting between I and an impersonal voice within one paragraph. |
| First person, high | Put the writer in view, about {n} first-person words per 100. | passive phrasing that hides the writer. |
| Questions, rare | Use questions sparingly, about {n} per 100 sentences. | rhetorical questions in a row. |
| Questions, occasional | Ask a question in about {n} of every 100 sentences. | questions in consecutive sentences. |
| Questions, frequent | Ask a question in about {n} of every 100 sentences. | long runs of statements with no question. |

## Step 8. Before and after
Output: the "Before and after" section with two labeled blocks. Skipped under the mixed-voice fallback (step 6).
- Before: a neutral three-sentence draft on the topic the user names. If no topic is named, go to the refuse list and ask.
- After: 40 to 80 words on the same topic that follow all six rules in lines 5 to 10.
- Measure the After block: words per sentence and contractions per 100 words. Both must fall in the same band as lines 1 and 3. If one does not, rewrite the After block once and report the second result. Do not rewrite a third time.

## Output contract
Use these headings in this order and nothing else before the first heading:

1. `## Status`: one value only: `complete`, `partial` or `stopped`. For partial, list the dropped sample IDs, or write none if no sample was dropped.
2. `## Intake`: table with columns Sample | Words | Sentences | Paragraphs.
3. `## Measurements`: table with columns Metric, one column per sample (S1, S2, S3 and so on), and Combined. Rows, in order: words per sentence, sentences per paragraph, contractions per 100 words, first person per 100 words, second person per 100 words, questions per 100 sentences, exclamations per 100 sentences. Then `### Connectors` with columns Connector, one column per sample, and Total.
4. `## Voice profile`: exactly ten numbered lines (step 7), or only lines 1 to 4 under the mixed-voice fallback (step 6).
5. `## Before and after`: `Before`, `After`, and `After measured:` with the two values. Omit this heading under the mixed-voice fallback.
6. `## Flags`: a list of codes from this table, or the word `none`.

| Flag | Meaning |
|------|---------|
| CLEANED | Text removed in step 2 |
| REDACTED | Personal number replaced with [redacted] |
| DROPPED | Sample under 100 words after cleaning, not used |
| UNSTABLE | A rate spread above 0.50 of the Combined rate |

Status meanings: `complete` means all samples were used and steps 7 and 8 finished. `partial` means one or more samples were dropped, the minimums still held, and the profile was written; or the mixed-voice fallback in step 6 applied, and only lines 1 to 4 were written. `stopped` means the minimums failed and only the question list is returned.

## Refuse / stop when
- The target is a named third party, a famous author or a living writer. Refuse the imitation, and offer a profile of the user's own samples only.
- The samples are not the user's own, and the user does not confirm authorship after one question. Drop the sample, then apply the minimums.
- Fewer than 3 usable samples or fewer than 600 words remain after cleaning. Return status `stopped` with the question list below.
- No topic is given for the before and after block. Return status `stopped` with the question list.
- The stated purpose is to pass the text off as another person's writing or to evade a detector. Refuse.

Question list format, returned as the whole reply when stopped:
1. Which samples are yours? Send each one labeled.
2. Can you add samples until the total reaches 600 words?
3. What topic should the Before and After blocks use?

## Limits
- Hand counts can be off by one per count. The Measurements table lists every count so the user can correct one and the bands can be redone.
- The profile describes measured style in the samples given. It does not judge quality and does not claim the samples represent the user's full range.
- All bands and the 0.50 stability value are working values.
