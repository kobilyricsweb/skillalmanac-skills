# Conclusion Paragraph Writer

## One line

Turns a supplied essay body and its thesis into a 70 to 110 word closing paragraph that restates the thesis, synthesizes three quoted points, and ends on one implication from the body.

## What it does

The skill works from the text you supply and nothing else. It first confirms that body text exists and locates the thesis, either as a sentence the body already states or as a thesis you give. It then picks three supporting sentences, each from a different body paragraph, and copies them verbatim into an extraction table. A fourth verbatim sentence, taken from the final paragraph, supplies the closing implication.

With those sources fixed, the writer drafts exactly three sentences. The first restates the thesis in new words, with no shared word run longer than four tokens. The second names the topic of all three points in one sentence. The third follows from the implication source. The draft is then checked against eight named checks covering length, sentence count, new facts, new numbers, new quotation marks, thesis overlap, synthesis coverage, and implication source. Failed checks trigger up to two rewrites before the output is marked partial.

The output has four headings: the conclusion, an extraction table, a check table with measured values, and a status line with open questions. Every number in the check table is a count that a reader can recompute from the body and the conclusion.

## When to use

Use it when a writer has a finished body and needs a closing paragraph that does not introduce new claims. It fits essays, opinion columns, and report sections where the conclusion should only echo what the body has already shown. It also fits drafts that have grown a conclusion that repeats the introduction word for word, because the thesis-overlap check catches long shared runs.

## When not to use

Do not use it to write an introduction, an abstract, a full essay, or a conclusion for text you have not supplied. Do not use it to critique an argument, decide whether a thesis is true, or add evidence. It will not produce a conclusion that needs a number, a citation, or a fact absent from the body, because those are refused.

## Requirements

No software, network access, or script. Any text-capable agent that can follow a numbered procedure and count whitespace-separated tokens can run it. The input is the essay body as plain text. A thesis is optional when the body states one.

## Example

Input body: a 441-token essay on remote work. The text is reproduced below so that every quotation in the output can be checked against it.

Remote work succeeds when companies replace visible presence with clear written expectations. For decades, managers measured effort by the people they could see at their desks, and that habit did not disappear when offices emptied. Many teams simply moved the same habits onto video calls, which left workers guessing about what counted as good work. The problem was never distance itself. It was the absence of agreed standards that everyone could read, check, and follow without asking a manager first.

The first requirement is a shared written record of decisions. When a choice is made in a hallway conversation, people who were not in that hallway learn about it late, or never. Teams that work well remotely keep short decision notes in a common place, with the date, the reason, and the owner of each choice. A new hire can then read six months of decisions in an afternoon instead of asking the same questions in five separate chats.

The second requirement is a clear agreement about response times. Without one, every message feels urgent, and people either answer everything instantly or feel guilty for not doing so. A team that writes down its norms, such as which channel is for urgent problems and which can wait until the next working day, removes that pressure. Workers can then plan long stretches of focused work without wondering whether they are failing someone.

The third requirement is measuring results rather than hours. When a manager can see a person online, time spent online becomes a stand-in for productivity, and that stand-in rewards the wrong behavior. Written goals tied to finished work, such as a shipped feature or a resolved support queue, tell both sides what success looks like. Performance conversations then start from evidence that anyone on the team can inspect.

None of this removes the real costs of distance. Some newcomers struggle to learn informally, and some people miss the social contact that an office provides. Companies that want to address those costs can schedule regular in-person gatherings and mentoring pairs, but these activities work best when they supplement written standards rather than replace them. Without written expectations, even well-meaning social events leave the same confusion in place.

Companies that expect remote work to succeed should therefore start with documents rather than with technology. Video platforms, chat tools, and tracking software all matter less than the basic question of whether a new employee could understand how the team operates from the written record alone. If the answer is no, the fix is not more meetings. It is clearer writing about decisions, responses, and goals, reviewed regularly and updated when the work changes.

Output:

## Conclusion
Remote teams do well when they trade physical proximity for shared written standards. Decision notes, agreed response windows, and goals tied to finished work let every member learn how the team operates by reading its own records, without relying on who happens to be online. The practical implication is that a company wanting remote work to last should start with clearer written records rather than with more tools or more meetings.

## Extraction
| Role | Quoted text (verbatim) | Body paragraph |
|---|---|---|
| Thesis | "Remote work succeeds when companies replace visible presence with clear written expectations." | 1 |
| Point 1 | "The first requirement is a shared written record of decisions." | 2 |
| Point 2 | "The second requirement is a clear agreement about response times." | 3 |
| Point 3 | "The third requirement is measuring results rather than hours." | 4 |
| Implication source | "Companies that expect remote work to succeed should therefore start with documents rather than with technology." | 6 |

## Check table
| Check ID | Result | Measured value | Note |
|---|---|---|---|
| C1 | pass | 71 | inside 70 to 110 |
| C2 | pass | 3 | three sentences |
| C3 | pass | not applicable | each claim traces to paragraphs 2, 3, 4, and 6 |
| C4 | pass | 0 | no digits; no number words |
| C5 | pass | 0 | no quotation marks in the conclusion |
| C6 | pass | 2 | shared run "remote work" |
| C7 | pass | not applicable | sentence 2 names decision notes, response windows, and finished-work goals |
| C8 | pass | not applicable | sentence 3 follows the paragraph 6 source |

## Status
Status: complete

## Open questions
None.

## Limits

The check table relies on counts a reader can repeat (tokens, sentences, digits, quotation marks, and the longest shared word run). It does not verify meaning. Checks C3, C7, and C8 are judgments about whether a sentence follows from a body sentence, and the skill does not confirm those judgments against an outside source. The thesis and points are the writer's reading of the body. A different reader could pick different sentences, and the skill has no way to tell which reading the author intended.

The skill does not check factual accuracy, tone, grammar, house style, or whether the body itself is correct. It does not measure whether the conclusion reads well, only whether it follows the rules. The word floor of 150 tokens for the body and the thresholds in the table are working values, not published standards.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
