# knowledge-article-split-plan

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when a complete knowledge article must be divided into maintainable units according to distinct user tasks, audiences, and content boundaries. Do not use for evidence-driven content refreshes, broad consistency surveys, or arbitrary length reduction without task-based restructuring.

## Task boundary

technical-docs-writer creates and audits documentation pages, and workspace-wiki-organizer proposes archive or merge actions across an exported wiki. knowledge-article-split-plan is specifically a non-executing plan for dividing one complete article by user task, audience responsibility, and maintenance boundary while mapping every heading exactly once.

## Try the independent synthetic example

Propose a split plan for this complete article. Audience: office staff. Tasks: connect to Wi-Fi; reset a Wi-Fi password. Headings and text: “Overview”—these two tasks are covered. “Connect”—select CorpNet, then enter your current password. “Reset and verify”—open the password portal, choose Reset, then reconnect to CorpNet with the new password. “Warning”—do not close the portal before confirmation. Constraint: “Reset and verify” and “Warning” must remain together. Existing URL: /wifi. Redirect convention: old URLs redirect to the overview. Owner for all content: IT Support. Do not rewrite or migrate content.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `aggregate_isolated_0bf9a6446ca83037`:

```text
{"units":[{"name":"Connect to Wi-Fi","purpose":"Guide office staff in connecting to CorpNet with their current password","audiences":["office staff"],"retained_sections":[],"moved_sections":["Connect"],"prerequisite_treatment":"No separate prerequisite is supplied; link back to the /wifi overview for shared orientation","boundary_rationale":"This section serves the distinct connection task and can be maintained independently"},{"name":"Reset a Wi-Fi password","purpose":"Guide office staff through resetting their password and reconnecting to CorpNet","audiences":["office staff"],"retained_sections":[],"moved_sections":["Reset and verify","Warning"],"prerequisite_treatment":"No separate prerequisite is supplied; link back to the /wifi overview and retain the confirmation warning with the reset procedure","boundary_rationale":"Password reset, reconnection, verification, and the governed warning form one task boundary; the hard constraint keeps Reset and verify with Warning"}],"shared_context":["Retain Overview at /wifi as the overview for both tasks, with links to the two task units"],"section_mapping":[{"section":"Overview","destination":"/wifi","status":"retained"},{"section":"Connect","destination":"Connect to Wi-Fi","status":"assigned"},{"section":"Reset and verify","destination":"Reset a Wi-Fi password","status":"assigned"},{"section":"Warning","destination":"Reset a Wi-Fi password","status":"assigned"}],"duplicate_risks":["Connecting to CorpNet and entering a password occurs in Connect to Wi-Fi, while reconnecting to CorpNet with the new password occurs in Reset a Wi-Fi password. Preserve the reset-specific reconnect step; use a cross-link to the connection unit if fuller connection instructions would otherwise be repeated."],"migration_checklist":["Draft separate task-unit proposals without rewriting source instructions","Keep Overview at /wifi and propose links from it to both task units","Keep Reset and verify and Warning together","Propose links from each task unit back to /wifi","Apply the supplied convention so any retired task URL redirects to /wifi","Have IT Support review ownership, boundaries, warnings, and proposed links","Review localization needs and link labels before any migration","Confirm every heading remains represented before publication"],"verification":["Every supplied heading has exactly one placement","Overview is retained only in shared context and is absent from unit section lists","Reset and verify and Warning remain together","The reconnect action is identified across the affected task units","The supplied /wifi URL, redirect convention, audience, and owner are preserved","No rewrite or migration is claimed"],"open_decisions":["Choose canonical URLs for the two task units","Confirm who performs final editorial review for IT Support","Determine whether localization constraints apply","Choose link labels and routing between /wifi and the task units"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
