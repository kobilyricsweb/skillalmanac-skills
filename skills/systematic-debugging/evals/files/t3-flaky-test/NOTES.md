The test `tests/test_cache.py::test_expiry_refresh` fails intermittently in CI. Over the last 40 CI runs it failed 5 times. Locally on the developer's laptop it passed 10 out of 10 runs.

The assistant's proposed fix: add `time.sleep(0.2)` before the assertion. It ran the test 3 times after the change, all passed, and wants to mark the bug fixed.
