## Contents

- Defaults and mutation
- Iteration and laziness
- Truthiness and comparison
- Exceptions and cleanup
- Evaluation order
- Numbers
- Imports and names

# Behaviour traps in "obvious" refactors

Python changes that look safe and are not. Read the section that matches what you are touching.

## Defaults and mutation

- A mutable default argument (`lines=[]`) is created once and shared by every call. Moving the default to `None` plus an `if` fixes a bug and changes behaviour: callers who relied on the shared state break. Leave it, report it.
- Changing a default value, even to an equal-looking one (`0` to `0.0`, `""` to `None`), changes what callers get when they omit the argument.
- Adding or removing a defensive copy of an argument changes whether the caller's object is mutated.

## Iteration and laziness

- Replacing a list with a generator expression makes the result single-use and moves side effects from call time to consumption time. It also removes `len()`, indexing and a second iteration.
- `map` and `filter` are lazy; a loop that appended to a list was eager.
- A comprehension has its own scope; a loop variable that the code used after the loop does not exist after the rewrite.
- Iterating a `set`, or removing items while iterating a list, depends on order; keep the data structure.
- `sorted` is stable; replacing a sort with `min` or `max`, or changing the key, changes which of several tied elements is returned.
- A `dict` keeps insertion order; a rewrite that goes through a `set` loses it.

## Truthiness and comparison

- `if x:` and `if x is not None:` differ for `0`, `""`, `[]` and objects with `__bool__` or `__len__`. Do not "simplify" one into the other.
- `==` and `is` differ for equal but distinct objects; keep the original operator.
- `a and b or c` is not the same as `b if a else c` when `b` can be falsy.
- A chained comparison (`a < b < c`) evaluates `b` once; splitting it evaluates `b` twice.

## Exceptions and cleanup

- Narrowing or widening an `except` clause changes what propagates. Removing a bare `except` or an `except Exception: pass` is a behaviour change.
- Guard clauses must not skip a `finally` block or a context manager exit that the nested version reached.
- Raising a different exception type, even a base class or a subclass, can break callers that catch it.
- Implicit `None` versus an explicit value: callers may test the result.

## Evaluation order

- Combining statements can reorder side effects: logging, I/O, counters, calls to the clock or a random generator.
- Short-circuit operators (`and`, `or`) and `any` and `all` skip later operands; a rewrite that removes the short-circuit runs them.
- Hoisting an expression out of a loop is safe only if it is pure and the loop body cannot change its inputs.

## Numbers

- Summing floats in a different order can change the last digits; compare against exact fixtures.
- `//` and `int()` round in different directions for negative numbers; `round` rounds halves to even. Keep the original operator.
- `/` versus `//`, `int` versus `float` results and a `Decimal` context are part of the observable result.

## Imports and names

- An import may exist for its side effect (registering a plugin, patching, setting a path). Unused-import removal needs a search for that.
- `__all__`, `from x import *` and re-exports make an apparently unused name public. Check `__init__.py` files and docs.
- A moved function can create a circular import, and import order can change which module's code runs first.
- Names may be reached through strings: `getattr`, entry points in packaging config, serialisation, templates, pytest fixtures matched by name.
- Decorators run at definition time, in order; moving or merging definitions can change registration order.
