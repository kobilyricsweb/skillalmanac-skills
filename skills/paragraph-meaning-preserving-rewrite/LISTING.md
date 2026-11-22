# Paragraph meaning-preserving rewrite

## One line

Rewrites one supplied paragraph in new wording, keeps every claim, number, name and date, and reports the proof as a claim table and before-and-after counts.

## What it does

The skill takes a paragraph of 20 to 300 words and splits it into numbered claims. It rewrites the paragraph claim by claim, then checks the result against the source. The output has four checks: a claim table that marks each claim kept or not, a count check that compares numbers, names and dates before and after the rewrite, a length check against a target band, and a settings table that records the tone and any length target the user gave.

The skill is strict about what changes and what does not. Tone, sentence structure and word choice may change. Every number, name and date must stay the same value. Modal verbs such as may and must, hedges such as about and roughly, and the referent of each pronoun are carried over. A request to add a fact or to change a figure is refused for that clause only, and the rest of the rewrite is still delivered with status partial. A request to rewrite text so that a plagiarism or AI-detection check will not flag it is refused as a whole.

## When to use

Use it when a writer has a paragraph that needs new wording for a newsletter, a product page, a caption or a summary section, and the facts must stay exactly as written. It fits short paragraphs of 50 to 150 words that carry a few figures and named people or organizations, such as a profile, a program update or a local news item.

## When not to use

Do not use it to add background, to correct a fact, to update a figure, or to fill a gap in the source. Do not use it to translate, to summarize several paragraphs into one, or to shorten a long article. It is not the right tool for text that is a table, code, or a bulleted list, because the claim split is built for prose. The skill will not help make text pass a plagiarism or AI-detection check.

## Requirements

A text-capable agent that can read the pasted paragraph and return Markdown. No script, no Python, no network access and no account are needed. The agent does the counting itself using the definitions in the skill, so the counts follow the rules in the file and not a library's word splitter.

## Example

Input paragraph (90 words, 3 numbers, 2 names, 0 dates):

> Maria Lopez started the neighborhood reading club in the spring with 12 members. By the end of the summer, the group had grown to 400 readers, and Jordan Blake, the library board chair, asked her to run a second session each week. She said the biggest surprise was how many teenagers signed up. She plans to add 2 volunteer tutors next fall, and she hopes to reach every school in the district. The club meets in the back room each evening, where volunteers read aloud and take turns leading discussion.

Output:

```
Status: complete

## Rewrite

Maria Lopez launched the neighborhood reading club in the spring, and it opened with 12 members. By the end of summer, the group had reached 400 readers. Jordan Blake, chair of the library board, then asked her to lead a second session every week. She said the biggest surprise was how many teenagers joined. Next fall she plans to bring in 2 volunteer tutors, and she hopes to serve every school in the district. The club meets each evening in the back room, where volunteers read aloud and take turns guiding the discussion.

## Claim table

| Claim | Original claim | Rewritten wording | Kept |
|---|---|---|---|
| C1 | Maria Lopez started the neighborhood reading club in the spring. | Maria Lopez launched the neighborhood reading club in the spring | yes |
| C2 | The club started with 12 members. | and it opened with 12 members | yes |
| C3 | By the end of the summer, the group had grown to 400 readers. | By the end of summer, the group had reached 400 readers. | yes |
| C4 | Jordan Blake, the library board chair, asked her to run a second session each week. | Jordan Blake, chair of the library board, then asked her to lead a second session every week. | yes |
| C5 | She said the biggest surprise was how many teenagers signed up. | She said the biggest surprise was how many teenagers joined. | yes |
| C6 | She plans to add 2 volunteer tutors next fall. | Next fall she plans to bring in 2 volunteer tutors | yes |
| C7 | She hopes to reach every school in the district. | she hopes to serve every school in the district | yes |
| C8 | The club meets in the back room each evening. | The club meets each evening in the back room | yes |
| C9 | Volunteers read aloud and take turns leading discussion. | where volunteers read aloud and take turns guiding the discussion | yes |

## Count check

| Category | Original | Rewritten | Match |
|---|---|---|---|
| Numbers | 3 | 3 | yes |
| Names | 2 | 2 | yes |
| Dates | 0 | 0 | yes |

## Length check

| Original words | Rewritten words | Ratio | Target band | Result |
|---|---|---|---|---|
| 90 | 93 | 1.03 | 72 to 108 | within |

## Settings

| Setting | Value |
|---|---|
| Tone | neutral |
| Length target | none given |

## Open questions

None
```

## Limits

The skill checks the three counted categories, plus the claim table the agent writes. It does not verify that the agent split the claims correctly. A missed claim would not show up in the counts, so a reader should compare the claim table against the source. Counting uses the written definitions, which cover digit numbers and common cardinal words. Unusual number forms, such as fractions written in words or dates written as "the third of May", may be missed or miscounted. Names are counted by the agent's judgment of proper nouns, not by a name list.

The skill does not verify meaning beyond the claim table. It cannot confirm that a hedge or a tone change has the same force as the source, that the rewrite reads well, or that a reader would take the same meaning from it. It does not check for plagiarism, AI-detection signals, copyright or deliverability. It does not check the facts in the source against the world, and it does not check whether the user is entitled to publish the text.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
