# Retry prompt contract

Use this when a record fails validation and the policy allows a retry. `--retry-out` writes the message text for every failed record, one JSON line each: `record`, `failure_classes`, `retry_message`.

## Rules

1. At most one retry per record. A second failure on the same record is not retried; it goes to a dead-letter store with both replies and both failure lists.
2. Retry only classes where the model can act: `invalid_syntax`, `duplicate_key`, `wrong_type`, `number_as_string`, `missing_field`, `extra_field`, `out_of_range`, `enum_violation`, `pattern_mismatch`, `length_violation`, `empty_array`, `array_size`, `no_json_found`. For `truncated`, raise the output limit before retrying; the same limit will cut it again. For `empty_output`, check the request first.
3. Same model, same settings as the first call, plus the conversation so far: the first prompt, the rejected reply as the assistant turn, then the retry message as the user turn. Do not paste the rejected reply into the message text.
4. The message lists the problems by field path, at most 8 lines of at most 160 characters each, then a fixed closing instruction. The script builds it; its shape is:

```
Your previous reply was rejected by the program that parses it.
Problems found:
- $.rating is the string "4", expected integer
Reply again with exactly one JSON value that satisfies the schema. Put nothing before or after it: no code fences, no comments, no explanation. Keep every value that was not listed as a problem unchanged.
```

5. Never put the model's likely excuse in the message ("you made a mistake"). State the fact and the required result.
6. Log per record: first failure classes, retry yes or no, retry result. Report the retry rescue rate (rescued / retried) next to the first-pass rate; a rescue rate under 50% means the message or the schema is unclear, not that more retries are needed.
7. Retries hide a prompt problem. Track the first-pass rate as the quality number; the post-retry rate is the delivery number.

## When not to retry

- The failure is deterministic (schema asks for something the input cannot provide): fix the schema.
- The reply is a refusal: do not push the model; route to a human or an error path.
- The cost of one extra call is higher than the cost of a dropped record: skip the retry and count the drop.
