Synthetic input: Steps are (1) “Submit form,” (2) “Enter email,” (3) “Confirm preview.” Dependencies: preview follows email; submission follows confirmation. Starting state: blank form. Expected end state: submitted form. All step text is immutable.

Concrete artifact:

1. “Enter email.”
2. “Confirm preview.”
3. “Submit form.”

Move log:

- Original 2 to new 1: preview dependency requires the email first.
- Original 3 to new 2: submission dependency requires confirmation first.
- Original 1 to new 3: submission is last under the supplied dependency.

Verification placement: “Confirm preview” remains before submission because the input explicitly makes confirmation a prerequisite; no additional verification action is invented.

Reachability note: the reordered steps begin at the blank form, enter the only supplied field, confirm the preview, and submit. The expected submitted state is supported by the stated dependency and the step names; no claim is made about unmentioned fields or server behavior.
