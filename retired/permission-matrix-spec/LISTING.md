# permission-matrix-spec

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when supplied role, resource, operation, condition, exception, and default-rule notes must be organized into an application permission matrix. Do not use for sequencing organizational approvals, inferring permissions from job titles, or changing access controls.

## Task boundary

Nearest is approval-path-mapper; this specifies application permissions rather than sequencing organizational approvals.

## Try the independent synthetic example

Build a documentary permission matrix. Roles: editor and viewer. Resource: report. Operations: read and delete. Statements: P1 from Policy A says editors may read reports; P2 from Policy A says editors may delete reports only when status=draft; P3 from Policy A says viewers may read reports. No statement allows viewers to delete. Explicit default rule D1 from Policy A: default deny for every unmentioned role-resource-operation combination. Conditions and exceptions: only P2's draft condition; no exceptions. Include evidence for every cell and do not alter or test access controls.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_11b1501fc455`:

```text
{"matrix_status":"complete","missing_dimensions":[],"cells":[{"role":"editor","resource":"report","operation":"read","status":"allow","condition":null,"evidence":["P1, Policy A"]},{"role":"editor","resource":"report","operation":"delete","status":"conditional","condition":"status=draft","evidence":["P2, Policy A"]},{"role":"viewer","resource":"report","operation":"read","status":"allow","condition":null,"evidence":["P3, Policy A"]},{"role":"viewer","resource":"report","operation":"delete","status":"deny","condition":null,"evidence":["D1, Policy A: default deny for unmentioned combinations"]}],"unresolved_conflicts":[],"assumptions":[],"scope_note":"Documentary model only; it does not alter or test access controls and does not establish runtime authorization behavior."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
