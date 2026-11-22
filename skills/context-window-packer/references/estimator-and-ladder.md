## Contents

1. Why a ratio and how wrong it can be
2. Calibrating your own ratio
3. Why the ladder is ordered this way
4. Placement inside the package
5. Sources

## 1. Why a ratio and how wrong it can be

A token is a piece of text produced by a model-specific splitter. Common English words are often one token, rare words and identifiers are several, and punctuation, indentation and non-Latin scripts cost more per character. A single characters-per-token ratio therefore moves with the kind of text:

| Kind | Ratio used | Stated error | Why |
|---|---|---|---|
| prose (`.md .txt .rst`) | 4.0 | plus or minus 20% | long common words, spaces cheap |
| code | 3.3 | 25% | short identifiers, symbols, indentation |
| data (`.json .yaml .csv .xml .html`) | 3.0 | 30% | quotes, braces, numbers, repeated keys |
| other or unknown | 3.5 | 30% | midpoint |
| non-ASCII characters | 1 token each | error raised to 40% when over 20% of the text | accents, CJK and emoji often split into several pieces |
| user-supplied ratio | as given | 10% | measured on the same material |

These values are working figures chosen to be slightly cautious for code and data. They were not measured against any tokenizer when this package was written. If a bill, a counter or an overflow error shows a different number, trust that number and use section 2.

Headers: each packed item gets a line `=== id: path [level] ===`; its cost is the line length divided by 3.5 and rounded up, counted inside the item.

## 2. Calibrating your own ratio

1. Pick three to five files that look like the candidates (same language, same mix of code and prose).
2. Count their tokens with the target model's own counter (a provider token-counting endpoint or a counter in the product). Do not use a different vendor's counter for an exact figure.
3. Divide the total character count by the total token count. That is the ratio.
4. Pass it as `"chars_per_token"` in the manifest or `--chars-per-token` on the command line. It replaces the per-type table for every file, so calibrate on a sample that matches the whole package.
5. If the package mixes prose and code very unevenly, run two packages or keep the table.

A calibrated ratio narrows the stated error to 10 percent in the report. It does not make it exact.

## 3. Why the ladder is ordered this way

- Full text comes first because any rewriting loses detail the user did not choose to lose.
- Signatures come second: they keep names and shapes, so the model can ask for the body or reason about calls, at a fraction of the cost. A form that is not clearly smaller (under 70 percent of full) is not worth the loss and is not offered.
- A stub only says that the file exists, how large it is and what its first line is. It is allowed for should items because a pointer lets the model or the user request the file next turn. It is not allowed for nice items because the tokens spent on the pointer buy nothing.
- Dropping is last. Dropping a must item is never done silently: the run reports an error so the user decides.
- Tiers are never mixed. A should item at stub level still ranks above a nice item at full level, since the user said which matters more; relevance only orders items inside a tier.

## 4. Placement inside the package

Long-context tests have found that models use material near the start and end of a long input more reliably than material in the middle. The script writes must items first, then should, then nice, and asks that the question go after the package. If one must item is the key document, place it last of the must group by listing it last in the manifest.

## 5. Sources

Facts here are restated in the author's words; the pages were not re-fetched when this file was written, so check the current text before quoting a figure.

- OpenAI help article "What are tokens and how to count them": https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them (source for the rule of thumb of about four characters per English token).
- Anthropic documentation on token counting: https://platform.claude.com/docs/en/build-with-claude/token-counting (counting with the provider's own endpoint, used for calibration).
- Liu et al., "Lost in the Middle: How Language Models Use Long Contexts": https://arxiv.org/abs/2307.03172 (position effect behind section 4).
