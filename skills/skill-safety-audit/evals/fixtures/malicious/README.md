# Inert malicious fixtures

Everything in this folder is deliberately bad **test data** for the skill-safety-audit scanner. None of it is runnable as stored:

- Every file has an extra `.txt` extension (`boot.py.txt`, `SKILL.md.txt`, `package.json.txt`), so no interpreter, package manager or skill loader will execute or install it.
- All hosts use the reserved `.invalid` suffix, so they cannot resolve.
- All credentials are fake placeholders (the AWS id is the public documentation example; keys, tokens and the PEM body are made up).
- The "payload" strings only print harmless text.

`evals/run_fixtures.py` copies each folder to a temporary directory, removes the trailing `.txt`, scans the copy with `scripts/skill_audit.py` and deletes the copy. To inspect a copy yourself: `python evals/run_fixtures.py --materialize <empty-dir>`. Never install or run the materialised copies.

Folders: `free-seo-booster` (many risks), `injection-awareness-guide` (quoted attack strings), `leaked-credentials` (literal secrets only).
