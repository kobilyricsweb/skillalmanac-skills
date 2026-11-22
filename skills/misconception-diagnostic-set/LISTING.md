# misconception-diagnostic-set

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when an instructor needs short probes that discriminate among explicitly supplied misconceptions and ordinary mistakes under a supplied governing rule. Do not use for general quiz generation, diagnosing a learner from one response, or resolving conflicting authoritative rules without stated precedence.

## Task boundary

classroom-quiz-builder produces a multiple-choice knowledge check from supplied source text. misconception-diagnostic-set instead creates compact probes keyed to an explicitly supplied governing rule and named misconceptions, recording alternative explanations and interpretation limits rather than diagnosing a learner from one response.

## Try the independent synthetic example

Create 2 diagnostic items for this objective: add fractions with equal denominators. Supplied misconceptions: M1, add both numerators and denominators; M2, multiply the numerators when adding. Correct rule: when denominators are equal, keep the denominator and add the numerators. Response format: select one of three choices and give one sentence of reasoning. For each item provide its correct response, targeted misconception, cautious distractor reasoning, alternative explanations, interpretation limit, and a follow-up probe if ambiguity remains.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `aggregate_isolated_c4c67f2814b7db9d`:

```text
{"status":"complete","objective":"Add fractions with equal denominators.","requested_count":2,"delivered_count":2,"shortfall_reasons":[],"items":[{"item_text":"Calculate 2/7 + 3/7. Select one: A) 5/14, B) 5/7, C) 6/7. Give one sentence of reasoning.","response_format":"Select one of three choices and give one sentence of reasoning.","correct_response":"B) 5/7. The denominators are equal, so keep 7 as the denominator and add the numerators: 2 + 3 = 5.","targeted_misconception":"M1: Add both numerators and denominators.","expected_distractor_reasoning":"Selecting A may be consistent with adding 2 + 3 for the numerator and 7 + 7 for the denominator.","alternative_explanations":["The learner may have confused fraction addition with another remembered procedure.","The learner may have selected the wrong choice accidentally despite using the correct rule."],"interpretation_limit":"A single selection or explanation cannot establish that the learner holds M1.","follow_up_probe":"Calculate 1/9 + 4/9 without choices, then explain specifically what happens to the denominator."},{"item_text":"Calculate 3/8 + 2/8. Select one: A) 6/8, B) 5/16, C) 5/8. Give one sentence of reasoning.","response_format":"Select one of three choices and give one sentence of reasoning.","correct_response":"C) 5/8. The denominators are equal, so keep 8 as the denominator and add the numerators: 3 + 2 = 5.","targeted_misconception":"M2: Multiply the numerators when adding.","expected_distractor_reasoning":"Selecting A may be consistent with multiplying the numerators, 3 × 2, while retaining the common denominator.","alternative_explanations":["The learner may have mistaken the addition sign for multiplication.","The learner may know the rule but have made an arithmetic or choice-selection error."],"interpretation_limit":"One response cannot distinguish a stable misconception from a sign-reading, recall, arithmetic, or selection error.","follow_up_probe":"Calculate 4/11 + 2/11 and explain whether the numerator operation follows the plus sign or another rule."}],"missing_inputs":[],"conflicts":[],"interpretation_limits":["Responses are evidence to investigate, not a diagnosis of a learner."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
