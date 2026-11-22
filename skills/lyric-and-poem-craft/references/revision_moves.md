## Contents

- Revision moves by flag
- Originality check, step by step
- Questions for the brief

## Revision moves by flag

Change one thing per pass, then re-run the audit. Keep the author's images and meaning; fix shape first.

| Flag | Move |
|---|---|
| line_length_uneven | Find the line furthest from the section median (see syllables_per_line). Cut filler words from a long line; give a short line one concrete detail. Do not pad with "oh", "yeah" or "baby". |
| verse_length_mismatch | Move a line into the shorter verse or fold two weak lines in the longer verse into one. |
| hook_repetition_low | Put the title phrase in the first and last chorus line, or repeat it once more inside the chorus. |
| hook_repetition_high | Replace one repeat with a line that adds a new fact or image. |
| hook_missing_in_chorus | The title must be sung in every chorus; rewrite the chorus around it. |
| chorus_drift | Decide: either make the later chorus identical to the first, or change the same line on purpose and keep the rest identical. |
| first_chorus_late | Cut the first verse to 4 to 8 lines or move the chorus up. |
| cliche / cliche_density | Replace the stock phrase with a specific image only this song could have: a named object, a place, a time of day. Keep a stock phrase only if the line twists it. |
| predictable_rhyme | Change the end word of one line so the rhyme becomes slant, or keep the pair and make the image around it fresh. |
| no_end_rhyme | Confirm the choice. If a rhyme was intended, the heuristic may have missed an irregular spelling: add `rhyme_like` in an overrides file and re-run. |
| form_check fail or check | Read the failing check's expected and actual values; fix the lines it names. For haiku, a one-syllable gap is often the heuristic: confirm by reading aloud. |
| syllable_uncertainty | Read the listed uncertain words aloud, then add true counts under `syllables` in the overrides file. |

## Originality check, step by step

The script cannot know whether a line exists in someone else's song or poem. This procedure is the check.

1. Before drafting, record what the author says the piece is based on. If it is "a song I love", the job is to write something new about the same feeling, not to reword that song.
2. Never use, quote, or rebuild existing lyrics from memory as source material, and do not paste a protected song into a file to compare against. The `--compare` option is for text the user supplies and is entitled to share, such as their own earlier drafts or a poem in the public domain.
3. Run the audit and open `originality.search_list`. These are the hook, the first chorus line and the longest lines that are not stock phrases.
4. Search each phrase in quotation marks, using a web search tool if one is available, otherwise ask the user to do it. Record the result for every phrase: no match, or the match found.
5. A match of 5 or more consecutive words in someone else's work means rewrite that line. A match of 3 or 4 words in a common phrase is acceptable if the rest of the line is different.
6. Check the chorus melody and rhythm claims separately: this skill treats words only, and the user remains responsible for the melody.
7. Report the search status honestly: "searched and clear", "not searched", or "match found at line N".

## Questions for the brief

Ask only what is missing, in one message:

- Form: verse-chorus, AABA, ballad, sonnet, haiku, limerick, rap, or free verse.
- Theme in one sentence, and the image or object the piece should turn on.
- Tone and point of view (first person, addressed to someone, a character).
- Title or hook phrase, if there is one.
- Will it be sung or read? Sung lyrics tolerate repetition; read poems need less.
