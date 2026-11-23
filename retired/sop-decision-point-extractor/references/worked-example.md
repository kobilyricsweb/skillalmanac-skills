Synthetic SOP:
- S1: “The Inspector inspects each package.”
- S2: “If the seal is intact, the Inspector accepts the package and the procedure terminates.”
- S3: “If the seal is damaged, the Inspector sends the package to the Supervisor queue and the procedure terminates.”
- S4: “Wet packages are not addressed.”
- Role boundary: the Inspector performs the inspection, acceptance, and sending actions stated in S1–S3. “Supervisor queue” is a destination; no Supervisor action is assigned.

Concrete artifact:
- Decision D1 trigger: after the Inspector inspects a package.
- Decision question: what documented seal condition applies?
- Branch 1: condition “seal is intact”; action “accept the package”; role “Inspector”; termination “procedure terminates”; supporting passage “S2.”
- Branch 2: condition “seal is damaged”; action “send the package to the Supervisor queue”; role “Inspector”; termination “procedure terminates”; supporting passage “S3.”
- Missing branch: condition “package is wet”; no action, role, or rejoin point is documented; supporting passage “S4”; missing-or-ambiguous note requests the governing action and continuation rule.
- Decision-level supporting passages: S1–S4.

Verification checks each documented branch against its own cited passage and uses the explicit role boundary for the Inspector’s actions. It does not assign work to the Supervisor merely because a Supervisor queue is named. It preserves the wet-package gap rather than filling it and does not infer that every non-intact seal is damaged or that wet packages must be rejected.
