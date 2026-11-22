# Worked Example

Synthetic example; steps and environment are invented for this illustration.

Input environment: “A local text editor is available.” No credentials or command-line tool are stated.

Steps:

- S1: “Create `settings.txt` with the project name.”
- S2: “Upload `settings.txt` to the workspace.”
- S3: “Confirm the workspace shows the project name.”

Expected artifact:

- S1 — knowledge: basic text editing; state: editor available, supplied; input: project name, missing; artifact: `settings.txt`; verification: file contains the project name; status: blocked by missing project name.
- S2 — knowledge: upload workflow; state: workspace access, unknown; input: `settings.txt` from S1; artifact: uploaded file; verification: upload success, not stated; status: blocked by unknown access and missing cue.
- S3 — knowledge: locating workspace content; state: uploaded file from S2; input: project name, inherited unknown; artifact: observation; verification: stated display check; status: dependent on S2.

Gap register: project name, workspace access, and upload verification are omitted. Late-introduction register: none. Verification report: all steps have statuses and artifact origins; no setup or upload was executed.

Scope assumptions: supplied steps and local editor only; no workspace access or successful execution assumed.

Dependency edges: project-name input→S1 settings.txt artifact; S1 settings.txt→S2 upload input; S2 uploaded state→S3 display-check prerequisite. These are proposed dependencies, not observed completed states.
