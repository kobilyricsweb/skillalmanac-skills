# Worked Example

Synthetic example only.

Input:

- Categories: `Fruit` = “items that are fruit”; `Drink` = “liquids consumed as beverages”.
- Items: `apple`, `tea`, `stone`.
- Assignments: apple→Fruit; tea→Drink and Fruit; stone has none.
- Constraint: categories are exclusive.

Expected artifact:

- Unassigned: stone, because no assignment is supplied.
- Conflicting membership: tea, because it has two categories under an explicit exclusivity rule.
- Weak definition: Fruit, because its definition repeats the category term and does not explain the criterion.
- No invented assignment for stone.
- Reviewer question: Is tea’s Fruit assignment intentional, or should one membership be removed?

The report does not validate category parentage or claim that stone belongs in a particular category.
