# Data problems: effect, treatment, what to tell the user

Read the entries that match the audit's findings.

## Total and subtotal rows inside the data

Effect: summing the column counts every amount twice (once in its row, once in the total). Averages are pulled toward the total.
Treatment: leave these rows out of every calculation. Use them only to reconcile: if the computed total differs from the file's total row, find which rows explain the gap (duplicates, text amounts the spreadsheet's own SUM skipped, rows added after the total was typed).
Tell the user: the row numbers, and whether the file's own total agrees with the computed one.

## Exact duplicate rows

Effect: inflated sums and counts.
Treatment: if a column should be unique per row (order ID, invoice number, ticket number), a repeat is an entry error; remove it. Without such a column, two identical rows can be two real events (two identical purchases on one day); keep them and give the figure both ways.
Tell the user: the row numbers and the size of the difference.

## Spelling variants of one category

Effect: "North", "north " and "NORTH" become three groups; each looks smaller than it is, and a ranking can flip.
Treatment: merge values that are equal after trimming spaces and ignoring case. Do not merge values that merely look similar ("Nth", "Northern"); list them as a question.
Tell the user: which variants were merged.

## Numbers stored as text

Effect: a spreadsheet SUM skips them without warning; sorting puts "1,200" before "300".
Treatment: read currency signs, thousands separators, percent signs and surrounding spaces as formatting. A value in brackets is negative in accounting notation. A percent keeps its face value (12% is read as 12).
Tell the user: how many cells and an example row, because their own formulas are probably skipping them.

## Blank numeric cells

Effect: treating a blank as zero lowers an average; skipping it hides missing data.
Treatment: leave blanks out and report the count. Never fill them in.
Tell the user: the count, and that the average is over filled cells only.

## Extreme values

Effect: one typo (45000 for 450) can dominate a total.
Treatment: keep the value in the main figure, give the figure without it, and ask. Remove without asking only when the value is impossible for the column (an age of 220).
Tell the user: the row, the value, the typical range, both figures.

## Mixed or ambiguous dates

Effect: 03/04/2026 is 3 April in most of the world and March 4 in the United States. Mixed formats in one column usually mean two people or two systems entered the data.
Treatment: the order is provable only when some value in the same format has a first or second part above 12. If not provable, do not group by month; ask. Named months ("Jan 20, 2026") and year-first dates are unambiguous.
Tell the user: the formats found and which reading was used.

## Repeated values in a column that should be unique

Effect: "how many customers" is overstated when one email appears twice with different capitals or a trailing space.
Treatment: count distinct values after trimming and ignoring case. Rows for the same key with different details are a question for the user (which one is current?), not something to resolve silently.
Tell the user: the raw count, the cleaned count, the rows involved.

## Header problems

Blank or duplicate header names, a title above the header row, or no header at all change which column a name refers to. State which row was taken as the header and refer to columns by letter when names repeat.

## Manual checks when the script cannot run

1. Sort a copy by each text column and look for a "Total" label and for near-identical neighbours.
2. Count rows, then count distinct rows; a difference means duplicates.
3. In a spare column test each amount cell with the spreadsheet's ISNUMBER function; FALSE means text.
4. Compare the column sum with and without the last row.
5. Look at the minimum and maximum of each numeric column.
