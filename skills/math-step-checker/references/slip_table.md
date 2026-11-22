# Slip table: what the script names and how to hint

Read the row for the `suspected_slip.name` you got. Give the level 1 hint first; levels 2 and 3 only when the learner asks again (see the hint ladder in SKILL.md). Examples use made-up numbers.

| Name | Typical wrong step | Level 1 (locate) | Level 2 (name the kind) | Level 3 (the line, corrected) |
|---|---|---|---|---|
| `sign_when_moving_term` | `2x + 3 = 11` to `2x = 11 + 3` | "Look at how the 3 crossed the equals sign." | "When a term changes side, the operation reverses." | `2x = 11 - 3` |
| `distribute_negative` | `10 - (x + 3)` to `10 - x + 3` | "Check what the minus sign in front of the bracket touches." | "A minus before a bracket changes the sign of every term inside." | `10 - x - 3` |
| `dropped_parenthesis` | `3(x + 2)` to `3x + 2` | "Compare how many terms the 3 was applied to." | "A factor outside a bracket multiplies each term inside." | `3x + 6` |
| `divide_only_one_term` | `(2x + 6)/2` to `x + 6` | "Did the division reach every term?" | "Dividing a sum divides each term (or the whole sum), not one term." | `x + 3` |
| `fraction_no_common_denominator` | `1/2 + 1/3` to `2/5` | "Try the same step with a picture of half a pizza plus a third." | "Fractions are added over a common denominator; the denominators are not added." | `3/6 + 2/6 = 5/6` |
| `exponent_rule` | `(x + 2)^2` to `x^2 + 4`; `sqrt(a + b)` to `sqrt(a) + sqrt(b)`; `a^2 * a^3` to `a^6` | "Test this step with x = 1: do both sides agree?" | "Powers and roots do not distribute over a sum; same-base products add exponents." | `x^2 + 4x + 4` |
| `operation_on_one_side_only` | `2x = 8` to `x = 8` | "Compare what happened to the left and right sides." | "Whatever is done to one side must be done to the other." | `x = 4` |
| `divided_by_expression_that_can_be_zero` | `x^2 = 3x` to `x = 3` | "Compare the solution lists before and after this step." | "Dividing by x loses the case x = 0. Move everything to one side and factor instead." | `x^2 - 3x = 0`, `x(x - 3) = 0` |
| `sign_error` (arithmetic) | `4 - 9 = 5` | "Check the sign of the result." | "The size is right; the result should be negative." | `4 - 9 = -5` |
| `decimal_place` | `0.3 * 0.2 = 0.6` | "Count the decimal places in the factors." | "The product has as many decimal places as both factors together." | `0.3 * 0.2 = 0.06` |
| `unit_conversion_factor` | `250 [cm] = 25 [m]` | "Compare the units on both sides." | "100 cm make 1 m, so divide by 100." | `250 [cm] = 2.5 [m]` |
| `truncated_not_rounded` | `2.6789 ~= 2.6` (one decimal place, cut instead of rounded) | "Look at the digit after the one you keep." | "Round by looking at the next digit; do not just cut." | `2.6789 ~= 2.7` |

## Statuses with no slip name

- `possibly_extraneous`: tell the learner a new solution appeared and ask them to substitute each candidate into the original equation. Radical and rational equations are the usual place.
- `solution_lost` without a matching row above: ask which line made a solution disappear.
- `unit_mismatch`: ask what the unit of each term is before adding.
- `rounded_unmarked` and `rounding_drift`: advise keeping at least two more digits than the final answer needs and rounding once, at the end.
- `not_equivalent` with `suspected_slip` null: say the step does not follow from the previous one, point at the line, and ask the learner to explain how they got from one line to the next.
