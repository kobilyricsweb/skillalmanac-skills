## Contents

- Order of the passes
- Numbers, money, dates, times
- Abbreviations and titles
- Symbols, URLs, e-mail
- Acronyms
- Timing model
- Chunking rules
- When to override a rule

These are the decisions `scripts/prep_voiceover.py` applies, written so the same result can be reached by hand. All rules are for US English.

## Order of the passes

1. Lexicon entries (protected from every later rule).
2. URLs, e-mail addresses, bare domains.
3. Dotted acronyms (U.S.), titles and abbreviations.
4. Dates, clock times, phone numbers.
5. Money, percent, negative numbers, `#` and `~` before digits, 24/7, simple fractions.
6. Ranges, units, decades, ordinals.
7. Plain symbols (and, plus, equals, at, hashtag).
8. Remaining numbers.
9. All-caps acronyms.

The order matters: a date must be read before its digits become a count, and money before the bare number inside it.

## Numbers, money, dates, times

| Written | Spoken | Rule |
|---|---|---|
| 1,200 | one thousand two hundred | commas group thousands; no "and" |
| 3.14 | three point one four | digits after the point are read one by one |
| 007 | zero zero seven | a leading zero means an identifier, read digit by digit |
| 10 or more digits, no commas | digit by digit | listed in `notes` as long_digit_string |
| 1984, in 2005, March 2026 | nineteen eighty-four, two thousand five, twenty twenty-six | four digits after in, since, by, until, till, from, before, after, during, year, circa, of, early, late, mid, a month name or "(" are years |
| 1500 steps | one thousand five hundred steps | no year context: a count, and listed in `notes` when 1100 to 2099 |
| 1990s, 2020s, 80s | nineteen nineties, twenty twenties, eighties | decades are plural |
| 1990-1995 | nineteen ninety to nineteen ninety-five | both ends four-digit years |
| 5-10 | 5 to 10 | digits then read normally; left alone if the left number is not smaller |
| 1st, 22nd | first, twenty-second | |
| $4.50 | four dollars and fifty cents | two decimals are cents; $0.50 is fifty cents |
| $2.5M, $1.2bn, $3k | two point five million dollars, one point two billion dollars, three thousand dollars | k, M, bn, B and the words thousand to trillion are scales |
| EUR sign, GBP sign | euros and cents, pounds and pence | same rule as dollars |
| 45% | forty-five percent | |
| -5 | minus five | only when the hyphen follows a space or starts the text |
| 3/4 | three quarters | denominators 2 to 10 only; other fractions stay and are reported |
| 24/7 | twenty-four seven | |
| #1 | number one | |
| March 3, 2026 | March third, twenty twenty-six | month first |
| 3 March 2026 | the third of March, twenty twenty-six | day first |
| 2026-03-03 | March third, twenty twenty-six | ISO date |
| 03/04/2026 | not read | order unknown; reported under `unexpanded`; ask the user which order was meant |
| 3:30pm, 9:00 am | three thirty P M, nine A M | minutes 00 are dropped, 01 to 09 are "oh five" |
| 14:05 | fourteen oh five | 24-hour; 14:00 is "fourteen hundred", 9:00 without am or pm is "nine o'clock" |
| (555) 123-4567 | five five five, one two three, four five six seven | ten digits in phone layout |
| 555-0100 | five five five, zero one zero zero | seven digits with a hyphen; a hyphenated 3+4 digit range such as 100-2000 would be read as a phone number, so write ranges with "to" |
| v2.1.3 | version two point one point three | v prefix with two to four dot-separated parts; bare x.y.z or x.y.z.w has no "version"; two-part 2.5 stays a decimal; pre-release tags such as -beta are not handled and remain in `unexpanded` |

## Abbreviations and titles

| Written | Spoken | Condition |
|---|---|---|
| Mr., Mrs., Ms., Prof., Sen., Rep., Gen., Capt., Col., Lt., Sgt., Rev. | Mister, Missus, Miz, Professor, Senator, Representative, General, Captain, Colonel, Lieutenant, Sergeant, Reverend | only before a capitalised name |
| Dr. | Doctor before a name; Drive after a capitalised word or number when no name follows | clash (both fit) reads as Doctor and is listed in `notes` |
| St. | Saint before a name; Street after a capitalised word or number when no name follows | same clash rule |
| No. 5 | number 5 | only before a digit |
| e.g., i.e., etc., vs., approx. | for example, that is, et cetera, versus, approximately | |
| Inc., Ltd., Corp., Co., Ave., Rd., Blvd., Jr., Sr., Mt. | Incorporated, Limited, Corporation, Company, Avenue, Road, Boulevard, Junior, Senior, Mount | full stop kept when a new sentence starts, so the pause survives |

## Symbols, URLs, e-mail

| Written | Spoken |
|---|---|
| & between words | and |
| + or = with spaces around | plus, equals |
| @name | at name |
| #tag | hashtag tag |
| and/or | and or |
| word/word | not read; listed as a symbol (the writer chooses "or", "and" or "slash") |
| https://www.example.com/a-b | example dot com slash a dash b (scheme and www dropped; digits one by one) |
| me@site.org | me at site dot org |

A URL with more than two path segments, any query or fragment, or over 40 characters is also listed under `long_urls`: no listener can follow it, so replace it with "link in the description".

## Acronyms

Read letter by letter, as built in: FBI CIA USA UK US EU UN AI TV CEO CFO CTO API URL HTML CSS SQL GPU CPU PDF USB SEO UI UX DNA HR IT PR VR AR ID PC DIY VIP ATM GPS LED LCD HD NBA NFL BBC CNN HTTP HTTPS JSON XML IP VPN SMS. A trailing s is kept (APIs becomes "A P Is").

Read as words, left alone: NASA NATO OK ASAP RAM LASER SCUBA RADAR UNESCO UNICEF COVID OPEC PIN AIDS ZIP.

Anything else in capitals (two or more letters) is listed under `unexpanded`. Typical decisions: FAQ (letters or words?), GIF, SQL (S Q L or sequel), SaaS. Shouted words in capitals should be lowercased in the source; the voice does not shout because of capitals.

## Timing model

Seconds = words divided by wpm times 60, plus 0.2 for each comma, semicolon, colon and dash, plus 0.5 at each sentence end, with 0.9 at each paragraph end instead of 0.5. Words are counted after expansion; a hyphenated compound counts as two. Report the range across 140 and 170 wpm when a deadline matters, because voices differ more than the model does.

## Chunking rules

1. Chunks are built from whole sentences, packed up to the limit; a paragraph break inside a chunk counts as two characters.
2. A sentence longer than the limit is cut at the last semicolon or colon, then comma, then before a conjunction (and, but, or, so, because, which, that), then at a space, always leaving at least 30 percent of the limit in the first piece. Each cut is listed in `mid_sentence_breaks`.
3. A voice restarts its intonation at every request, so a mid-sentence cut sounds like a new sentence. Rewrite the sentence instead when it matters.

## When to override a rule

- A year that is really a count (1500 steps) is already handled; a count that is really a year in a context the list misses needs the lexicon (`"1984": "nineteen eighty-four"`).
- A name that contains an abbreviation read differently from the rule (for example "Ave. Maria" meant as Ave Maria): add a lexicon entry for the full written name.
- Foreign names: add a lexicon entry; use `ipa` when the tool supports phoneme tags.
