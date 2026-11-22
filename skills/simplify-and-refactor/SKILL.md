---
name: simplify-and-refactor
description: Runs behaviour-preserving refactors and cleanups of existing code, with characterisation tests first, one named transformation per commit, and a script that compares the before and after versions of a Python file for changed public signatures, removed names and import changes. Use when the user says clean up this code, simplify, refactor, tidy, reduce duplication, split this big function, or when an agent's cleanup changed behaviour or churned style. Do not use for bug fixes, new features, performance tuning, framework or dependency migrations, or rewrites in another language.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only, and no network. Without Python, follow the manual fallback in step 6.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
  author_model: claude-sonnet-5-5
  license: Apache-2.0
---

# Simplify and refactor

A refactor changes structure and nothing a caller can observe. Callers observe return values, raised exception types, side effects and their order, public names and signatures. If any of those move, the change is not a refactor: split it out and label it.

## Rules

1. No refactor on code you cannot test. If tests are missing, write characterisation tests first (step 3).
2. One transformation per commit, named from [references/transformations.md](references/transformations.md). Each commit leaves the tests green.
3. Never edit a test to make a refactor pass. A red test after a refactor means revert and rethink.
4. Do not fix bugs, rename public things, bump dependencies or reformat untouched code in the same change. Record each as "Found, not fixed".
5. Preserve quirks. If the old code truncates, swallows an error or mutates its argument, the new code does too, until the user asks otherwise.

## Workflow

Copy this checklist:

```
- [ ] 1 Scope: goal, files, what stays out
- [ ] 2 Baseline: tests run, starting version saved
- [ ] 3 Characterisation tests, green on unchanged code
- [ ] 4 Pick one transformation, check its preconditions
- [ ] 5 Apply, run tests, commit
- [ ] 6 Compare with refactor_diff.py; repeat 4-6
- [ ] 7 Final comparison against the starting version, report
```

1. **Scope.** Write one sentence for the goal ("split `process_order` into the steps it already performs"). List the files in scope. Anything the user did not mention is out of scope; the list of what never belongs in a refactor is in [references/transformations.md](references/transformations.md) under "Not a refactor". If "clean up" is the whole request, pick the smallest set of changes that removes duplication or nesting in the named file, and say what you chose.
2. **Baseline.** Create a branch or note the starting commit. Run the existing tests and record the result. If they already fail, list the failing tests and refactor only code they do not cover, or stop and ask. Save the starting version of each Python file in scope under a scratch path (for example `git show <start>:path/to/mod.py > <scratch-dir>/mod_before.py`).
3. **Characterisation tests.** For each function you will touch that lacks tests: call it with typical inputs, boundary inputs (empty, zero, one, maximum) and inputs that reach every branch; run it; assert the value it actually returns, the exception type it actually raises and the side effects it actually has (calls to collaborators, mutated arguments). Do not assert what it should do. Name the test file or class `characterisation` so a later reader knows these pin current behaviour. Run them on unchanged code: they must pass. Break one line temporarily to confirm a test goes red, then restore it. Dependencies you cannot call (network, clock, randomness) are replaced with fixed fakes inside the test, not changed in the code.
4. **Pick one transformation.** Look up its preconditions in [references/transformations.md](references/transformations.md); read only the entries you use. If a precondition does not hold (the extracted block assigns to two outer variables, the function is called by name from another file), choose a smaller transformation or stop and ask. Read [references/behaviour-traps.md](references/behaviour-traps.md) when the change touches defaults, iteration, truthiness, exceptions, evaluation order, numbers or imports.
5. **Apply and commit.** Make exactly that change. Run the full test suite, not only the new tests. Commit with the message `refactor: <transformation> <target>` and a body that says "no behaviour change". Do not run a project-wide formatter in this commit.
6. **Compare.** For each changed Python file run:

   ```bash
   python scripts/refactor_diff.py <scratch-dir>/mod_before.py path/to/mod.py
   ```

   Read the JSON (fields below). `surface_preserved: false` means a public name or signature moved: undo it, or isolate it in its own commit that the user approved. Run the script; do not edit it to make a check pass. Without Python, run `git diff -U0` and read every changed `def`, `class`, `import` and `__all__` line by hand.
7. **Final report.** Run step 6 once more between the starting version and the final file, run the full tests, and answer in this fixed shape:

```
Goal: <one sentence>
Commits: <list of "transformation on target", in order>
Behaviour: <tests green before and after; characterisation tests added: N>
Public surface: <surface_preserved value and any import changes from the script>
Found, not fixed: <bugs, risky code, naming problems, with file and line>
Not checked: <e.g. other files importing the changed names, dynamic access, performance>
```

## Script: scripts/refactor_diff.py

Run it. It parses both files with `ast`, writes nothing and prints one JSON object. Exit 0: public surface preserved. Exit 1: surface changed. Exit 2: unreadable file, syntax error or wrong arguments (JSON with an `error` field).

Output fields:

- `verdict`: `ast_identical` (only comments, whitespace or formatting changed), `surface_preserved`, or `surface_changed`.
- `surface_preserved`, `ast_identical`: booleans.
- `removed_public_names`, `added_public_names`: sorted lists; methods appear as `Class.method`.
- `possible_renames`: pairs `{from, to}` where a removed and an added name have the same signature.
- `changed_signatures`: list of `{name, kind, before, after, changes, breaking}`; `changes` holds items such as `param_removed:x`, `required_param_added:x`, `default_changed:x`, `param_order_changed`, `async_changed`, `class_header_changed`.
- `imports`: `{added, removed}`, normalised statements.
- `top_level_definitions`: `{preserved, only_in_before, only_in_after}` over functions, classes and module variables.
- `bodies_changed`: names whose statements differ, ignoring docstrings. This is where behaviour could have moved; the tests decide.
- `public_surface_source`: `__all__` or `no_underscore_rule`.

Public means: the names in a literal `__all__`, otherwise every top-level name without a leading underscore.

## Limits

- The script sees one file at a time. It cannot find callers in other files, dynamic access (`getattr`, plugins, reflection) or monkeypatching; search the repository for each renamed or removed name yourself.
- `surface_preserved: true` does not mean behaviour is preserved. Only the tests show that, and characterisation tests only cover the inputs you chose.
- The script handles Python only. The procedure and catalogue apply to other languages; there the comparison in step 6 is manual.
- The catalogue lists safe transformations; it is not exhaustive and it does not decide whether a refactor is worth doing.
- Code with randomness, clocks, concurrency or external services needs fakes and may stay partly untested; say so under "Not checked".
