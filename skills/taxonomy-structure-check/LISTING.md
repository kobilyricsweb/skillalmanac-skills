# taxonomy-structure-check

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when you need to check whether supplied id and parent_id records form a structurally sound rooted forest. Do not use for judging taxonomy meaning, keyword coverage, SEO strategy, or deciding how categories should be named.

## Task boundary

workspace-wiki-organizer finds orphaned or broken relationships in an exported knowledge structure, while architecture-diagrams validates graph readability and connectivity. taxonomy-structure-check is limited to the rooted-forest shape of supplied id/parent_id records, reporting roots, missing parents, self-parenting, and cycles without judging category meaning.

## Try the independent synthetic example

The interpreter is unavailable. Produce a labeled manual, unexecuted structural assessment of this exact input without running or editing the bundled script: {"nodes":[{"id":"r","parent_id":null},{"id":"a","parent_id":"r"},{"id":"b","parent_id":"x"},{"id":"c","parent_id":"d"},{"id":"d","parent_id":"c"}]}. Check only roots, orphan references, self-parenting, and cycles. Report execution mode and untested limits without judging category meaning.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_0c09cbaf959c`:

```text
Assessment type: manual and unexecuted; the interpreter and bundled script were not run.

Input validation: structurally valid for the supplied extract: unique nonempty string IDs, valid parent_id values, and five nodes.

Roots: ["r"].
Orphan references: [{"id":"b","parent_id":"x"}].
Self-parenting: none.
Cycles: [["c","d"]].

Conclusion: the bounded structural audit has findings, so it would correspond to a findings result rather than a clean pass. Scope is limited to roots, absent parent references, self-parenting, and parent-pointer cycles in this extract. Category meaning, naming quality, completeness, permissions, external truth, and live state were not assessed. Script exit code and exact CLI output are untested because execution was unavailable.
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
