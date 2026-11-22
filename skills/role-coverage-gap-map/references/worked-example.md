Synthetic input: Responsibility “Reviewer” is required from 09:00 to 12:00, with time zone unspecified. Ana is assigned and available 09:00–10:30. Bo is assigned and available 11:00–12:00. Rule R1 explicitly permits Ana and Bo to perform the Reviewer responsibility during their respective assigned intervals. No backup rule or additional availability is supplied.

Artifact:
- 09:00–10:30: assigned Ana; supplied availability and permission under R1 apply; status covered.
- 10:30–11:00: no supplied assignment or availability; status uncovered gap; action requiring review: provide coverage or revise the window.
- 11:00–12:00: assigned Bo; supplied availability and permission under R1 apply; status covered.

Review note: There is no overlap because the supplied intervals are separated by a gap. No backup is asserted, and no role substitution or schedule change is made. The unspecified time zone remains an input issue.
