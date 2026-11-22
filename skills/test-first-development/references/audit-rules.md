# Audit rules for scripts/test_audit.py

Read this when a finding is unclear or you suspect a false positive. Contents: rules, what counts as an assertion, what counts as trivial, skip reasons, scope.

## Rules

| Rule | Severity | Fires when |
|---|---|---|
| NO_TESTS | error | No recognised test in the file |
| NO_ASSERTION | error | A test has zero assertions |
| TRIVIAL_ASSERT | error | Every assertion in the test is trivially true (and there is at least one) |
| DUPLICATE_BODY | error | A later test has the same body as an earlier one (tests with zero assertions are skipped here; they already fail NO_ASSERTION) |
| SKIP_NO_REASON | error | Skip, conditional skip, expected-failure or skip-call without a written reason |
| ONLY_LEFT | error | A JavaScript `.only`, `fit` or `fdescribe` remains; the other tests are silently not run |
| NAME_CONTRACT | error | The name breaks the contract in SKILL.md, or fails a supplied `--name-regex` |
| ASSERT_HEAVY | warning | More than 6 assertions in one test |

## What counts as an assertion

- Python: an `assert` statement; a call whose attribute or name starts with `assert` (`self.assertEqual`, `mock.assert_called_once_with`, `assert_valid(x)`); `pytest.raises` and `pytest.warns`.
- JavaScript: `expect(`, `assert(` and `assert.<name>(`, `.should`, AVA `t.is(`, `t.deepEqual(` and similar, and `.expect(` as used by HTTP test clients.

## What counts as trivial

- Python: `assert True`, `assert 1`, any truthy constant; `assert not False`; `assert x == x` (same expression on both sides, also `is`, `<=`, `>=`); `assertTrue(True)`, `assertFalse(False)`, `assertEqual(a, a)`, `assertIs(a, a)`.
- JavaScript: `expect(<literal>)` for a boolean, null, undefined, number or string literal; `expect(x).toBe(x)` with the same identifier; `assert(true)`; `assert.equal(a, a)`.

## Skip reasons

- Python: `reason="..."` on `pytest.mark.skip`, `skipif`, `xfail`; a text argument on `unittest.skip`; the second argument of `skipIf` or `skipUnless`; a text argument to `pytest.skip()` and `self.skipTest()`. Empty strings do not count. `pytestmark = ...` at module level is checked the same way.
- JavaScript: a comment of the form `// skip: <reason>` or `// reason: <reason>` (or `/* skip: ... */`) on the line of the call or the previous non-blank line. A reason needs at least 3 non-space characters.

## Scope

- Python test = a function whose name starts with `test` at module level, or in a class named `Test*` or deriving from a `*TestCase`.
- JavaScript test = a call to `it`, `test`, `xit`, `xtest`, `fit`, `ftest` with a string title; `describe` blocks are checked only for skip and only findings.
- Names in the output are the function name (with the class prefix) or the JavaScript title.
