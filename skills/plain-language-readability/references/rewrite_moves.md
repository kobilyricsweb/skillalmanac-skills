# Rewrite moves and a worked example

Read the section that matches the finding you are fixing. Do not read it all up front.

## Contents

- Structure moves
- Vocabulary moves
- Obligation and permission words
- Defining a needed term
- Worked example

## Structure moves

| Finding in the report | Move | Check before you keep it |
|---|---|---|
| `long_sentences` (over 25 words) | Split where the sentence joins two ideas (and, which, that, because, but). Give each sentence one idea. Keep every condition (if, unless, except) in the sentence with the instruction it limits. | Read the first half alone: is it still true and still complete? If an exception got separated from its rule, move it back. |
| Action buried at the end | Put the thing the reader must do, and its deadline, at the start: "Send the form by 14 June." | The date and the actor are unchanged. |
| Sentence opens with a long "if" clause of 15+ words | Shorten the condition or move it after the instruction. | The condition still applies to the whole instruction. |
| Run of parallel items inside a sentence | Make a list, one item per line, same grammatical shape. | No item was merged or dropped; the lead-in sentence still says "all of" or "any of" as before. |
| A paragraph that mixes a rule, an exception and a contact | One paragraph per job. Put the contact last. | Nothing moved out of the scope of its heading. |
| Heading that names a topic ("Appeals") | Optionally turn it into the question the reader has ("How do I appeal?"). | Heading text is not a place to add new facts. |

Do not split sentences only to lower the grade. If the average sentence falls under 8 words the script warns; read the result aloud and rejoin pieces that now sound like a list of fragments.

## Vocabulary moves

| Finding | Move | Check |
|---|---|---|
| `rare_words` with a `plain` suggestion | Swap when the plain word fits the sentence. | A swap must not change a legal or technical meaning ("terminate" a contract is not always "end" a service). Words on the keep list are never swapped. |
| `wordy_phrases` | Use the shorter form (in order to / to, prior to / before, in the event that / if). | "Subsequent to" and "prior to" refer to time; "before" and "after" keep that. |
| Noun form of a verb ("make a determination", "give consideration to") | Use the verb ("decide", "consider"). | The subject of the new verb is the same actor. |
| Stack of nouns ("benefit payment recovery proceedings notice") | Unpack with small words: "a notice that we will start to recover the benefit you were overpaid". | The unpacked form says who does what. Do not add facts to make it flow. |
| `passive` with `agentless: true` | Name the actor only if the original text, or the organisation's own rules, say who it is. | If the actor is unknown, keep the passive and list it under "Left for the author". |
| `passive` with a "by" agent | Make the agent the subject. | Tense and modal unchanged. |
| Third person "the recipient" in a letter to that person | "You". Keep third person in rules about other people. | Whether "you" would include people the original did not address. |
| Acronyms | Spell out once, then use the short form. | Do not invent an expansion; use the one in the source or flag it. |

## Obligation and permission words

Meaning-critical. The script lists every modal count change as a warning; confirm each one against this table.

| Source word | Plain rewrite | Rule |
|---|---|---|
| must, shall (an obligation) | must | "Shall" to "must" is the usual plain-language edit when the source means an obligation. |
| must not, shall not | must not | Never soften to "should not". |
| should | should | A recommendation. Do not harden to "must". |
| may (permission) | can, or may | "You may appeal" can become "You can appeal". |
| may (possibility) | might, could | "Payments may stop" can become "Payments might stop". Never "will stop". |
| may not | ambiguous | It can mean "is not allowed" or "might not". Ask the author, or keep and flag; do not guess. |
| is required to, is obliged to | must | Same obligation. |
| will (a promise by the organisation) | will | Keep. A promise becoming "may" weakens a commitment. |

## Defining a needed term

A term the audience needs (a form name, a legal word, a scientific term the lesson is about) stays. The stop rule is: keep the term, define it once at first use in 15 words or fewer, then use it without repeating the definition.

Patterns the script's gloss check recognises after the term: a bracketed gloss `(...)`, "means", "is a", "are the", "refers to", a colon, or a spaced dash; and "called" or "known as" right before the term. Examples: "a deductible (the amount you pay before we pay)", "the amount you pay first, called a deductible".

## Worked example

Source (public notice, grade 11.1, 3 sentences over 25 words):

> In the event that a recipient is in receipt of a payment that exceeds the amount to which they are entitled, the Department will commence recovery proceedings subsequent to the issuance of a written notification.

Moves used: phrase swap (in the event that / if), noun form to verb (is in receipt of / was paid), third person to "you", split the actor out, passive to active ("we send"), plain swaps (commence / start, subsequent to / after, issuance of a written notification / we send you a letter).

Rewrite:

> If we paid you more than you are entitled to, we will start to recover the extra money after we send you a letter.

Facts check: no number in this sentence; "will" kept as "will"; the condition (if overpaid) stays attached to the action (recover). The Department becomes "we": allowed only because the notice is written by the Department; confirm with the author.
