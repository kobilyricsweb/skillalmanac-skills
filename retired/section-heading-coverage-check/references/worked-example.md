Synthetic input:
- Hierarchy: H1 is the parent of S1.
- H1 heading: “Costs and limitations.”
- Content directly assigned to H1: “This guide summarizes the service.”
- S1 heading: “Costs.”
- Content directly assigned to S1: “The annual plan costs $120. Monthly billing costs $12.”
- Protected headings: none.
- Required topics: costs and limitations.

Assign `heading-1` to H1 and `heading-2` to S1. These locators identify artifact rows; H1 and S1 remain the supplied section IDs.

| Row | ID | Promised element | Element status | Direct supporting content | Missing or conflicting evidence |
|---|---|---|---|---|---|
| heading-1 | H1 | Costs | Absent | None | Complete direct content supplies no costs |
| heading-1 | H1 | Limitations | Absent | None | Complete direct content supplies no limitations |
| heading-2 | S1 | Costs | Covered | Annual price $120; monthly price $12 | None |

H1 aggregate status is absent. Its heading is overbroad relative to its direct content. Descendant note: `heading-2` (S1) supplies cost information, but that descendant content is not direct support for H1. Bounded repairs are to narrow the unprotected H1 heading to match its direct summary content, reposition supplied cost content into H1, or propose adding limitation content once support is supplied.

S1 aggregate status is covered. No heading repair is needed.

Required-topic assessments:
- Costs: covered by `heading-2` (S1), with appropriate-heading status `yes` because “Costs” promises the supported topic.
- Limitations: absent because this complete synthetic document supplies no limitation content. Its appropriate-heading status is `unresolved`: H1 promises limitations, but there is no supporting content whose placement can be assessed.

Evaluative boundary: if a protected heading promises “Benefits and Risks” but its complete direct content says only “The device is lightweight,” assess benefit as unresolved because the attribute is not identified as beneficial, and risk as absent. The aggregate is unresolved. Do not infer a benefit, invent a risk, or alter the protected heading.

Verification report: every promised element and required topic is assessed separately. S1 directly supports its own cost promise and the required cost topic. Its prices are not transferred to H1. No supplied section supports limitations. The audit does not treat that gap as proof that the service itself has no limitations.
