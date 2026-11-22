## Contents

1. Splitting rules that give MECE branches
2. Common MECE failures and fixes
3. Confidence rubric and ceilings
4. Pyramid and so-what rules, with examples
5. Source notes

## 1. Splitting rules that give MECE branches

Pick one rule per level and say which in the node text or a note.

| Question type | Splitting rule | Example children |
|---|---|---|
| Why did a number change | Formula | Profit = revenue - cost; revenue = volume x price; volume = customers x purchases each |
| Should we do X | Criteria, each answerable yes/no | Market attractive; we can win; economics work; risks acceptable |
| How do we reach a goal | Process steps in order | Awareness, consideration, purchase, retention |
| Where is the problem | Segment, using a partition | Region (all regions listed), channel, customer size band |
| What is going on over time | Time slices without gaps | Before launch, launch to month 3, after month 3 |
| Internal or external cause | Inside / outside the company's control | Own pricing, own operations; market demand, competitors, regulation |

Only formula and process splits are exhaustive by construction. Segment and criteria splits need the `universe` list written out before the children are named; that is the check.

## 2. Common MECE failures and fixes

| Failure | Sign | Fix |
|---|---|---|
| Overlap by mixed rules | "Pricing", "Competitors", "Online" at one level | Re-split by one rule; move "Online" to a lower level |
| Overlap by nesting | A child is a subset of a sibling ("Customers" and "Enterprise customers") | Make the subset a grandchild |
| Gap hidden by "other" | An "Other" child with no size | State the share it may hold; otherwise list the missing segment |
| Single child | One branch under a node | Add the missing sibling or collapse the node |
| Wishlist level | 8 or more children | Group into 3 to 5 headings first |
| Verb branches | "Cut cost", "Raise price" | Split first by what is true (drivers), then derive actions |
| Tautology | Child restates the parent | Delete the level |

Tag hygiene: tags are short nouns, lower case, unique per node, and the same tag may reappear at other levels. A tag owned by two siblings is flagged `tree-overlap`; a tag in the universe that no child owns is flagged `tree-gap`.

## 3. Confidence rubric and ceilings

Score each evidence row by how it would hold up if challenged.

| Score | Meaning | Typical row |
|---|---|---|
| 0.9 to 1.0 | Primary measurement, checked, current | Own database export with the query saved |
| 0.7 to 0.89 | Reliable and traceable, small doubts | Audited filing; peer-reviewed study that fits the case |
| 0.5 to 0.69 | Plausible, partly traceable | One expert interview; industry report with unclear method |
| 0.3 to 0.49 | Weak | Single anecdote; blog post; back-of-envelope estimate |
| below 0.3 | Do not rely on it | Rumour; unverifiable claim; model output with no source |

Ceilings the script applies by `source_type` (warning above): assumption 0.4, estimate 0.7, interview 0.8, published_study 0.9, filing 0.95, primary_data 1.0.

Rules of use:
- Lower the score for age (data older than the decision cycle), for a different population than the question, and for a source with a stake in the answer.
- A hypothesis is "supported" only with at least one supporting row at 0.5 or more and a recorded search for refuting evidence. Several 0.3 rows do not add up to a 0.7 row.
- Refuting evidence at 0.7 or more flips the status unless the supporting rows are clearly stronger; say why in the write-up.

## 4. Pyramid and so-what rules, with examples

Pyramid rules (answer first, then grouped support):
1. The top of the document is the answer to the question asked, not a description of what was done.
2. Each level answers the "why?" or "how do you know?" that the level above raises.
3. Supporting points at one level are the same kind and are listed in a stated order.
4. Section titles read alone form the argument; test by reading only the titles.
5. Three to five points per level; more means regroup.

Executive summary contract (150 words at most):
- Sentence 1 is the answer, with the key number.
- Next 2 to 4 sentences are the reasons, one each, matching the section titles.
- Final sentence is the action, owner and date, or the decision needed.
- Forbidden: method narrative ("we analysed"), background the reader knows, hedges stacked on the answer.

So-what rule: every section ends with one line that says what changes for the reader. It must name an action, a decision, a risk or a belief that should change. It is not a recap of the section.

| Weak (label or recap) | Strong |
|---|---|
| "Freight costs are important." | "Renegotiate the two freight contracts that expire in March; they carry 70% of the increase." |
| "As shown, churn is high in month 1." | "Put the retention effort into the first 30 days; later months are stable." |
| "Competitors are active." | "Do not match the rival's price cut; our segment does not respond to price." |

## 5. Source notes

The answer-first grouping, same-kind points and ordering rules follow the pyramid principle described by Barbara Minto in her book The Pyramid Principle. The mutually-exclusive, collectively-exhaustive test and hypothesis-driven problem solving are standard practice taught in management consulting; this file restates the ideas in original words and adds the tag-based check, the confidence ceilings and the word limits, which are this skill's own working values.
