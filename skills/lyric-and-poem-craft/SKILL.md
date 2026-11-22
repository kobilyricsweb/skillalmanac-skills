---
name: lyric-and-poem-craft
description: Audits and coaches a writer's own original song lyrics and poems with a script that counts syllables per line, detects rhyme scheme, rates line-length regularity, finds repeated hooks and stock phrases, checks chorus consistency and section balance, and verifies forms (verse-chorus, AABA, ballad, sonnet, haiku, limerick, rap bars). Use when the user is writing their own lyrics or verse and says fix my chorus, does this rhyme, count the syllables, is my haiku 5-7-5, tighten my bridge, too cliche. Do not use to copy, continue or imitate an existing song or a named artist's lyrics, to write from memory of a published text, or to clear rights.
license: Apache-2.0
compatibility: The audit script needs Python 3.9 or newer, standard library only. No network access is used by the script. Without Python, follow the manual steps in section 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Lyric and poem craft

Help a writer shape their own lyric or poem: structure, line length, rhyme, repetition, freshness. You coach and revise; the images, story and voice stay the writer's.

## Originality rule (hard)

- Write and revise original work only. Never reproduce, continue, paraphrase closely or "swap a few words in" an existing song, poem or a named artist's lyrics, even if the user pastes it or asks for "in the style of, but different".
- Imitating a genre, form or mood is fine (a sad country ballad, a drill-style verse). Imitating a specific artist's text, signature lines or hook is not.
- If the request is a near-copy, decline that part in one sentence and offer a new piece on the same theme.
- Do not use any lyrics archive, including this site's, as a source for generation.
- Before calling a piece finished, run the originality check in step 6.

## Workflow

```
- [ ] 1 Brief: form, theme, tone, title or hook
- [ ] 2 Draft or receive, with section labels, saved to a file
- [ ] 3 Run the audit
- [ ] 4 Read the report against the tables below
- [ ] 5 Revise one issue type at a time, re-run
- [ ] 6 Originality check
- [ ] 7 Report
```

1. **Brief.** Fix the form (verse-chorus, AABA, ballad, sonnet, haiku, limerick, rap, free verse), a one-sentence theme, tone, and the title or hook phrase. Ask only what is missing. Section lengths and rhyme targets per form are in [references/form_specs.md](references/form_specs.md); read only the row for the chosen form.
2. **Draft or receive.** Save text to a file with section labels alone on a line: `[Verse 1]`, `[Chorus]`, `[Bridge]`. A second `[Chorus]` with no lines under it counts as a repeat. A file with no labels is split into blocks at blank lines (right for sonnets, ballads, haiku). Backing vocals in (parentheses) are left out of counts.
3. **Audit.**

```bash
python scripts/audit_lyrics.py draft.txt --form verse-chorus --title "hook phrase"
```

   `--form` is verse-chorus, aaba, ballad, sonnet, haiku, limerick, rap or none (default). `--title` sets the hook phrase counted in each chorus. `--overrides f.json` fixes syllable counts and rhymes the heuristic gets wrong (`{"syllables": {"fire": 2}, "rhyme_like": {"wind": "find"}}`). `--lines` adds per-line detail. `--compare other.txt` finds word runs shared with a text the user supplies. Run it; do not edit the script to make a check pass. Without Python, count syllables by clapping, mark end sounds by ear, and apply the same tables by hand.
4. **Read the report.** Strict JSON; key fields below. Every value is a heuristic: confirm by reading aloud before changing the writer's line.
5. **Revise.** Fix in this order: form and section shape, then line length, then hook and chorus, then clichés and rhymes. Revision moves per flag are in [references/revision_moves.md](references/revision_moves.md). Change the smallest thing that clears the flag, keep the writer's images, and re-run until the warnings are fixed or knowingly kept.
6. **Originality check.** Open `originality.search_list`. Search each phrase in quotation marks, using web search if available; otherwise ask the user to. A run of 5 or more consecutive words that matches someone else's work means rewrite the line. Record each phrase as searched-clear, searched-match or not searched. The full procedure is in the originality section of revision_moves.md.
7. **Report** in this fixed shape:

```
Form and brief: <form, theme, hook>
Audit: <warn count, info count; the three biggest issues with line numbers>
Changed: <what was revised and why>
Kept on purpose: <flagged items the writer chose to keep>
Originality: <phrases searched and result, or "not searched">
Not checked: <melody, stress and meter, rights clearance, anything the script cannot hear>
```

Give the revised text first, then the report.

## Report fields (script output)

| Field | Meaning |
|---|---|
| `sections[].syllables_per_line` | Heuristic count per line; `syllable_stdev` is the spread |
| `sections[].meter_regularity` | regular if at least 85% of lines are within 1 syllable of the section median; loose from 60%; else irregular. Syllable counts only, stress is not analysed |
| `sections[].rhyme_scheme` | Letters for perfect and identical rhymes, X for a line that rhymes with nothing found; `rhyme_scheme_with_slant` also links near rhymes |
| `sections[].rhyme_types` | counts of perfect, identical, slant and internal rhymes |
| `repeats` | repeated lines, repeated 3 and 4-word phrases, and `hook` with counts per chorus against the 2 to 4 target |
| `chorus_consistency` | similarity of each later chorus to the first (1.0 identical) |
| `section_balance` | lines by section type, verse lengths, lines before the first chorus |
| `cliches` | stock phrases found, from a fixed bundled list (`--list-cliches` prints it) |
| `form_check` | status pass, check or fail with each check's expected and actual value |
| `originality` | search list for step 6; `compare` result when `--compare` was used |
| `flags[]` | `severity` warn or info, `code`, `section`, `line`, `message` |

## Thresholds behind the flags

| Flag | Fires when |
|---|---|
| line_length_uneven | syllable stdev above 2.5 in a verse, chorus, bridge or stanza of 3 or more lines (3.5 for rap) |
| section_length | lines outside the hard limits (verse 2 to 12, chorus 2 to 10, bridge 1 to 8); info when only outside the usual range |
| verse_length_mismatch | verses differ by 2 or more lines |
| first_chorus_late | more than 16 lyric lines before the first chorus |
| hook_repetition_low / high | title phrase in a chorus fewer than 2 or more than 4 times; absent from a chorus is `hook_missing_in_chorus` |
| chorus_drift | a later chorus has similarity from 0.5 up to just under 1.0 to the first |
| cliche_density | more than 1 stock phrase per 8 lines |
| form_check | haiku exactly 5-7-5 (within 1 per line is `check`); limerick AABBA with 7-10, 7-10, 5-7, 5-7, 7-10; sonnet 14 lines matching a known scheme with 9 to 11 syllables; ballad quatrains 8-6-8-6 with lines 2 and 4 rhyming; AABA four sections; rap verses of 8 to 16 bars with at least 60% of lines rhymed |

## Limits

- English only. Syllables come from a vowel-group rule that misses some words (for example "somebody" is counted as 4, a speaker says 3); use overrides.
- Rhyme keys come from spelling. They over-match unstressed endings (baby and lady), can match words that only look alike (mountain and rain), and miss irregular spellings and rhymes across word endings (road and showed).
- Meter is syllable regularity, not stress. A line can be regular here and still limp when read aloud.
- Short texts (under 8 lines) give noisy statistics. The cliché and predictable-rhyme lists are partial.
- The originality step depends on a real search. The script reports candidate phrases and, with `--compare`, overlap with a text the user supplies; it cannot know whether a line exists elsewhere and gives no rights clearance.
- Melody, performance and genre feel are outside this skill.
