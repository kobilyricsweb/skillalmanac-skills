---
name: regex-from-labeled-examples
description: Proposes a Python regular expression from labeled match and non-match strings, then proves it against every supplied example in a row-by-row table. Use when a user has example strings that should match and others that should not and wants a regex that separates them, or wants an existing regex checked against labeled cases. Lists ambiguous cases that need more examples. Do not use for regexes written from a prose spec with no examples, for tuning patterns on large files, or for claims that a pattern is correct for unseen inputs.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Regex from labeled examples

Use this procedure when the user supplies strings labeled MATCH and NON-MATCH. The deliverable is one proposed Python regex and a proof table that tests the regex on every supplied example. The proof covers only those examples. It says nothing about other inputs.

## Workflow

1. Intake. Split the examples into two columns, MATCH and NON-MATCH. Assign IDs E01, E02, and so on, in the order the user gave them within each column, with MATCH rows first. Copy every example byte for byte; do not trim, lowercase, or correct it. In the table, write a pipe character as \| so the table stays valid. Output: the Columns table.
   - Stop if there are fewer than 3 MATCH rows or fewer than 3 NON-MATCH rows. Set Status to partial and write the missing rows as numbered Open questions.
   - Stop if the same string appears in both columns. Set Status to partial and ask which label is right.
   - Stop if a label is anything other than MATCH or NON-MATCH, unless the user states the mapping for each label word, such as YES or valid.
2. Plain-words rule. Write one sentence that names the feature all MATCH strings share and that every NON-MATCH string lacks. A feature is a length, a fixed prefix, a character class, a separator, or a position. Output: the Plain-words rule sentence.
   - If no single feature separates the columns, set Status to fail and stop after this step.
3. Propose the regex. Use Python re syntax. Anchor with ^ and $. Use [0-9] instead of \d, because \d also matches other Unicode digits. Evaluate with re.fullmatch, so a trailing newline never counts as a match. Number capture groups left to right. Add a capture group only around a part the user named or the plain-words sentence names; a pattern with no groups gives "[]" in the Groups column for each match. Output: the Regex block.
   - Refuse any pattern that breaks a rule in the pattern rules table below. Rewrite it, and count the rewrite.
   - After a rewrite, show only the final pattern. Earlier patterns are not shown. Each rewrite is counted on Status line 3.
4. Proof table. Evaluate every example, MATCH and NON-MATCH, with re.fullmatch. Record the captured groups as a list from group 1 onward, or "-" when there is no match. Compare the actual label with the expected label. Output: one row per example, in ID order.

   Row procedure, applied to each example in turn:
   - (a) Apply re.fullmatch to the example exactly as copied in the Columns table.
   - (b) If it matches, set Actual to MATCH and copy the groups as strings, or write "[]" when the pattern has no groups. If it does not, set Actual to NON-MATCH and Groups to "-".
   - (c) Set Expected from the Label column.
   - (d) Set Pass to yes only when Actual equals Expected. Count the yes rows for the Status line.
   - If any row fails, return to step 3 and rewrite. Allow at most 2 rewrites. If rows still fail after 2 rewrites, set Status to fail and list the failing IDs under Open questions.
5. Ambiguous cases. List 2 to 5 strings the user did not supply that the pattern decides only by an arbitrary choice. Good candidates are trailing whitespace, a lowercase version of a fixed uppercase prefix, a digit count one away from the examples, a non-ASCII digit, and an empty string. Choose only candidates whose outcome the plain-words sentence does not already settle. For each, state what the pattern decides and which example the user should label. Output: the Ambiguous cases table.
6. Generality statement. Write the count of supplied examples and state that the regex is proven only on them. Output: the last line of the Status section.
7. Status. Set the value from the decision table below.

Pattern rules (working values, not published specs):

| Rule | Limit |
|---|---|
| Quantified group that contains a quantifier, such as (a+)+, (\w*)*, or (a\|a)* | Never allowed |
| Alternation where two branches can match the same string | Never allowed |
| Number of quantifiers in the pattern | At most 6 |
| Pattern length in characters | At most 120 |
| Lookbehind or backreference | Only when a MATCH example needs it |

Decision table:

| Condition | Status | Where it stops |
|---|---|---|
| Fewer than 3 MATCH rows or fewer than 3 NON-MATCH rows | partial | After step 1 |
| Same string in both columns | partial | After step 1 |
| No single feature separates the columns | fail | After step 2 |
| Rows still fail after 2 rewrites | fail | After step 4 |
| Every proof row passes, with ambiguous candidates listed as questions; or a refused clause | partial | Runs to the end |

Precedence: when several rows apply, the most severe status wins, in the order fail, then partial. Write one status value only. The skill never reports ok, because step 5 always lists ambiguous candidates, and a clean run still ends as partial to show that more labels are needed.

Words to avoid when describing the pattern: always, guaranteed, complete, correct for all, and safe. Describe the result only as passing or failing on the listed rows.

## Output contract

Use these headings in this order and no others. Start the output with the Status heading, with no preamble, and end it with the Open questions section.

- `## Status`: line 1 is `Status: partial` or `Status: fail`. Line 2 is `Passed N of M examples.` Line 3 is `Rewrites used: R of 2.` Line 4 is one sentence stating that the regex is proven only on these M examples.
- `## Columns`: table with columns ID, Label, Example. Label is MATCH or NON-MATCH.
- `## Plain-words rule`: one sentence.
- `## Regex`: one fenced code block holding the pattern on one line, then the line `Flags: none`.
- `## Proof table`: columns ID, Label, Example, Expected, Actual, Groups, Pass. Expected and Actual are MATCH or NON-MATCH. Pass is yes or no. Groups is a list such as ['100234'], "[]" for a match with no groups, or "-" for a non-match.
- `## Ambiguous cases`: columns Candidate, Pattern decides, Example to label. Write "None." when the list is empty.
- `## Open questions`: numbered list. Write "None." when empty. Required when Status is partial or fail.

Table rules:
- IDs in the Proof table are the IDs from the Columns table, in the same order. Do not renumber, skip, or add IDs.
- The Ambiguous cases table holds 2 to 5 rows. Fewer than 2 rows means step 5 was skipped; go back and complete it.
- Each Open questions item names one example ID, one ambiguous candidate, or one refused clause, and one missing fact. Ask one question per item.
- Write strings in the Columns and Proof tables with no added quote marks. Write strings in the Ambiguous cases table in double quotes, so that trailing spaces and empty strings stay visible.

## Refuse or stop when

- Fewer than 3 MATCH or fewer than 3 NON-MATCH rows: stop after intake, Status partial, numbered list of what is missing.
- The same string is labeled both ways: stop after intake, Status partial, ask which label is right.
- No feature separates the columns: Status fail, no regex is proposed.
- The user asks that the regex be "general", "complete", or "correct for all inputs": refuse that claim only. Keep the rest of the deliverable, set Status partial, and list the refused claim under Open questions.
- The user asks for nested or overlapping quantifiers for speed or for a catch-all: refuse that clause only. Propose the nearest pattern that obeys the pattern rules, set Status partial, and list the refused clause under Open questions.
- Any examples are missing a label: stop after intake and ask for the label under Open questions.
- A label word other than MATCH or NON-MATCH is used and the user has not mapped it: stop after intake, Status partial.

## Files

The package ships this file and the license text in [LICENSE.txt](LICENSE.txt). No script ships with this skill. The procedure is applied by reading the examples and the pattern, and the proof table is worked out row by row.
