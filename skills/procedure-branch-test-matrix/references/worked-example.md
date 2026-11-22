Synthetic input: The procedure says x>=5 leads to goA and x<5 leads to goB. The input domain is integer x. No missing-value rule, precedence rule, or execution environment is supplied.

Artifact:
- Case T1: x=5; x>=5 is true; expected path goA; status covered boundary.
- Case T2: x=4; x<5 is true; expected path goB; status covered lower side.
- Case T3: x=6; x>=5 is true; expected path goA; status covered above boundary.
- Missing-value behavior: unknown and uncovered because no rule was supplied.

Review note: The matrix uses synthetic inputs only. It does not claim that the procedure ran, does not infer null handling, and does not add a default action. The two conditions cover the supplied integer cases shown.
