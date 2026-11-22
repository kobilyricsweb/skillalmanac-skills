## Contents

- How to read an entry
- Catalogue (12 transformations)
- Not a refactor
- Sources

# Transformation catalogue

Each entry gives when the change is safe (preconditions), the steps, and the check that proves it. Names follow common usage in the refactoring literature; the wording is original.

## How to read an entry

All preconditions are required. If one fails, pick a smaller transformation or ask. "Callers" means every use of the name in the repository, found by search, plus any documented public use.

## Catalogue

### 1. Rename (private, local or parameter)
Preconditions: the name is local, private (leading underscore), or a parameter that no caller passes by keyword; the new name is unused in that scope and does not shadow a builtin or an import.
Steps: rename the definition and all uses in one edit by tool or exact search; search again for the old name in strings, comments and tests.
Check: tests green; script shows no `removed_public_names`.

### 2. Extract function
Preconditions: the block is a contiguous run of statements; it assigns at most one outer variable (return it) and reads the rest as parameters; it contains no `return`, `break`, `continue`, `yield` or `await` that targets the enclosing code; it does not rebind an outer variable through `nonlocal` or `global`.
Steps: copy the block into a new private function whose parameters are the outer values it reads; replace the block with a call; keep the evaluation order of arguments.
Check: tests green; the new name is private, so the script lists no added public name.

### 3. Inline function
Preconditions: the function has one caller or a trivial body; it is private; no decorator, no recursion, no keyword use from tests.
Steps: replace the call with the body, substituting parameters; for arguments that have side effects, evaluate each once into a local first.
Check: tests green.

### 4. Extract variable
Preconditions: the expression has no side effects, or it is evaluated exactly once both before and after.
Steps: give the expression a name used where it appeared; keep the name in the narrowest scope.
Check: tests green.

### 5. Inline variable
Preconditions: the variable is assigned once, used once, and nothing between assignment and use changes what the expression reads.
Check: tests green.

### 6. Replace nested conditionals with guard clauses
Preconditions: the branches are mutually exclusive; each early exit returns or raises exactly what the original path did; no `finally` or context manager depends on reaching the end.
Steps: invert one condition at a time, exit early and dedent the rest; run the tests after each inversion.
Check: tests green; branch coverage of the function unchanged.

### 7. Consolidate duplicated branches
Preconditions: two branches contain identical statements that do not depend on the branch condition and are not order-sensitive relative to the condition's side effects.
Steps: move the shared statements before or after the conditional.
Check: tests green.

### 8. Replace manual loop with comprehension or built-in
Preconditions: the loop only builds one collection or aggregate; no `break`, no early exit, no side effects in the body; the result type stays the same (list stays list); element evaluation order is kept; for float sums the summation order is kept (see behaviour traps).
Steps: write the comprehension, then run the characterisation tests including the empty input.
Check: tests green.

### 9. Remove dead code
Preconditions: a repository-wide search finds no reference by name, string, config or reflection; the code is not a public name or entry point; no test imports it. Removing an import also needs proof that the module is not imported for its side effects and not re-exported.
Steps: delete only what the search proved unused; one group of deletions per commit.
Check: tests green; the script lists the removal under `removed_public_names` or `imports.removed`, so it is a conscious decision.

### 10. Replace magic literal with named constant
Preconditions: the same value and meaning appear at each replaced site (two equal numbers with different meanings get different names or stay as they are).
Steps: define the constant at module level, private unless it is part of the API; replace each site.
Check: tests green; `top_level_definitions.only_in_after` shows the new constant and nothing else.

### 11. Move function or class within a module
Preconditions: the move changes no import-order effect, no decorator registration order and no definition-time dependency (a default value or base class defined later).
Steps: move the definition, leave its name unchanged.
Check: tests green; `top_level_definitions.preserved` is true.

### 12. Split a module and re-export
Preconditions: every public name is re-exported from the original module, so `from old import name` still works; no circular import appears; module-level side effects keep their order.
Steps: create the new module, move the definitions, import them back in the old module, list them in `__all__` when one exists.
Check: tests green; a smoke test imports each public name from the old module path.

## Not a refactor

Do not mix these into a refactor commit. Report them as "Found, not fixed", or do them in their own labelled change when the user asks:

- bug fixes, including obvious ones (off-by-one, a mutable default argument, a swallowed exception)
- renaming or re-signaturing public functions, classes, CLI flags, config keys, environment variables or serialised field names
- changing error messages, log text, exception types or return types
- performance work and caching
- dependency, language-version or framework upgrades
- formatting, import sorting or linting of lines you did not otherwise touch
- adding type hints, docstrings or comments to code you are not changing
- adding features or handling new cases "while I was there"
- deleting tests or loosening assertions

A public rename that the user does ask for gets its own commit: add the new name, keep the old one as an alias, update callers, and remove the alias only when the user says so.

## Sources

Catalogue idea and names: https://refactoring.com/catalog/ (read for naming only). The term characterisation test comes from Michael Feathers, Working Effectively with Legacy Code (book). Python facts behind the preconditions: https://docs.python.org/3/reference/compound_stmts.html#function-definitions and https://docs.python.org/3/library/ast.html.
