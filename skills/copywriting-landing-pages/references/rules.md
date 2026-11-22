# Landing-page audit rules

Read the section that matches a finding from `scripts/lp_audit.py`, or read the whole file when you cannot run the script.

## Contents

- Thresholds and why
- Section role detection
- Numeric claims: what is detected and what is exempt
- Accepted source patterns
- Banned phrases
- CTA label patterns
- Reading level proxy
- Facts and where they come from

## Thresholds and why

| Constant | Value | Reason |
|---|---|---|
| Headline words | warn over 12, error over 14, warn under 3 | A promise that fits one breath is read in full; under 3 words is usually a slogan with no outcome |
| Hero support words | warn over 30, error over 45 | One sentence under the headline; more turns the hero into a section |
| Section heading words | 10 | A heading is scanned, not read |
| Paragraph or list item words | 50 | Roughly three short sentences; beyond that the line is two messages |
| Section words | 150 default, 180 how, 300 objections, 150 proof, 60 cta | Per-section budgets that keep each section to one message |
| Sub-headings per section | 4, except how and objections | Many sub-headings mean the section is a mini-page |
| CTA label words | 2 to 5 | Verb plus object; longer labels read as sentences |
| Primary CTAs | 4 per page, 2 per section, 2 wordings | One action, repeated; not a menu |
| Reading grade | warn over 8, error over 10 | General-audience copy; business jargon pushes the grade up quickly |
| Long sentence | 25 words | Reported for the first 5 only |

These are working values drawn from common copy practice. They are not fitted to conversion data. Change a limit only for a stated reason, and say so in the report.

## Section role detection

The script reads each H2 heading, tests the role patterns in this order, and the first match wins: objections (faq, questions, pricing, guarantee, risk, "what if"), how (how it works, steps, process, setup), proof (proof, customers, testimonials, results, case study, reviews), cta (get started, start, try, sign up, book, ready, join, request, contact). The H1 section is the hero. A last section of 60 words or fewer that holds a link and matched nothing is treated as the CTA section. Anything else is `other`.

Order check: the first occurrence of each present role must follow hero, proof, how, objections, cta. A section out of order is a warning, a missing section is an error unless named in `--optional`.

## Numeric claims: what is detected and what is exempt

Detected: percentages (61%), multipliers (3x, 3 times faster), currency amounts, counts of people or organisations (212 freelancers, 5,000 teams), time claims (in 5 minutes, saves 10 hours, 3 days faster, 4 hours a week), ratings (4.8/5, 5 stars), ranks (#1, No. 1, top 10).

Exempt, because they are terms and not performance claims:

- A currency amount followed by a billing period (`$12/month`, `$9 per user`) or preceded by from, starting at, only, costs, pricing, plan.
- A percentage, money or time figure within 40 characters of the words trial, refund, money-back, guarantee or cancel (trial length, refund window). Terms still need to match the billing system.
- Years, dates, version numbers, step numbers, phone numbers and a bare count without a people or organisation noun.

Always an error, number or not: "thousands of", "millions of", "hundreds of", "countless", "numerous", "a growing number of", "many companies/teams/customers/businesses/brands", "trusted by many/leading/top/the best".

## Accepted source patterns

A numeric sentence passes when any of these is present in it, or the sentence that follows within the same paragraph is a citation, or the next paragraph starts with a citation:

1. An external `https://` link whose text does not begin with a CTA verb (get, start, try, book, request, join, sign, download, buy, subscribe, create, schedule, claim, talk, contact, shop, order, begin).
2. `Source:` or `Sources:` followed by a name and date.
3. `according to ...`.
4. A footnote marker `[^id]` whose definition line `[^id]: ...` exists in the document. A marker with no definition does not count.
5. A citation of the form `(Author, 2025)`.
6. `as of <month> <year>` or `n = <count>`.
7. A block quote followed by an attribution line that starts with a dash and a capital letter.
8. In HTML, a superscript number linked to an in-page anchor.

The script only checks that a source is present. It does not open links or read the source.

## Banned phrases

Each is flagged by pattern. Severity `error` means an unsubstantiated claim; `warn` means a style problem.

| Group | Phrases and variants | Severity | Replace with |
|---|---|---|---|
| Hype verbs | revolutionize/revolutionary, game-changer/game-changing, supercharge, turbocharge, skyrocket, unleash, unlock the (full) power or potential, elevate, empower, leverage | warn | The concrete change: what the visitor can do that they could not before |
| Empty adjectives | cutting-edge, state-of-the-art, next-gen, world-class, best-in-class, groundbreaking, unparalleled, unrivalled, unmatched, industry-leading, market-leading, robust, powerful, innovative, disruptive, holistic, synergy | warn | A spec, a number with a source, or nothing |
| Ease words | seamless, effortless, frictionless, simply, "just click/add/sign" | warn | The actual steps and how long they take |
| Filler openers | "in today's fast-paced / digital / competitive world", "take your X to the next level", "next level" | warn | Start with the visitor's problem |
| Category blur | all-in-one solution or platform, one-stop shop, end-to-end solution, no-brainer | warn | List the three things it covers |
| Superlatives | the best, best on the market, best in the world, number one | error | A named ranking with date and source, or cut |
| Guarantees | guaranteed, guarantee results/success/growth/ROI, risk-free, 100% satisfaction/safe/secure/accurate, zero risk | error | The written refund or cancellation term |
| Social proof without counts | many users/people/businesses love/trust, loved by many/thousands | error | The count and its source |
| Pressure | act now, limited time, don't miss out, last chance, hurry, while supplies last, only N spots/seats left | warn | Allowed only with a real deadline that has a date in the same sentence |
| Vague CTA | click here | warn | A verb plus an object |

A phrase inside a direct quotation from a named customer is still flagged; decide by hand whether to keep it, because the quote is theirs and the claim must still hold.

## CTA label patterns

A link counts as a CTA when its title is `cta`, its text starts with a CTA verb, it matches a vague label, or it stands alone on its line, is not an in-page anchor and has 1 to 6 words. HTML buttons count always. In-page anchors (`#how`) are secondary and are not counted or compared.

Label problems reported: vague label (submit, click here, here, learn more, read more, more info, go, continue, send); does not start with a verb; fewer than 2 or more than 5 words; trailing `!` or `...`; all caps.

## Reading level proxy

Flesch-Kincaid grade = 0.39 x (words / sentences) + 11.8 x (syllables / words) - 15.59. Computed over paragraphs and list items (not headings, not CTA-only lines), each list item counted as one sentence. Syllables are counted by vowel groups with a silent-e correction, so the grade can be off by about a grade level. Under 40 words the grade is `null`.

## Facts and where they come from

- Flesch-Kincaid grade formula and its origin in a 1975 US Navy training study: https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests
- US advertising law expects an advertiser to hold the evidence for an objective claim before making it, which is the basis of the "no source, remove the number" rule; the FTC's plain-language guide for small businesses: https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business
- Research on how people read web pages (they scan, and short plain text is read more than long text): https://www.nngroup.com/articles/how-users-read-on-the-web/
- The one-action, one-destination rule and the word limits are editorial conventions of this skill, not legal or research findings.
- Pages above were not re-fetched while this file was written; treat the descriptions as summaries to confirm before quoting them.
