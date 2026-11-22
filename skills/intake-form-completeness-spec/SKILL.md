---
name: intake-form-completeness-spec
description: "Use when an intake workflow needs field-level requirements that vary by request type and must be tied to supplied routing, format, validation, and incomplete-case rules. Do not use for configuration-key comparison, generic form redesign, data diagnosis, or making fields mandatory merely because they seem useful."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.6"
  network: none
---

Specify an intake form from supplied request types, candidate fields, routing needs, format rules, optionality rules, validation sources and results, and incomplete-case policy.

Create one field record per candidate field and one nested rule for every declared request type. If no request type is declared, retain the field records with empty request-type rule arrays, record the missing request types in `gaps`, and keep completeness unresolved. Each declared-type rule states applicability, requiredness, absent-or-invalid handling, and source trace.

Record purpose, format, validation source, and validation-result status at field level when shared. When one varies by request type, put the type-specific value in that request-type rule; it overrides the field-level value for that type. Keep the field-level property concise or state that it varies. Do not repeat unchanged shared values.

Make a field mandatory only when a supplied rule requires it. Otherwise use optional, conditional, prohibited, not applicable, unspecified, or unresolved only when supported. Distinguish not applicable from missing, and do not treat missing information as false. Keep presence and format checks separate from validation outcomes. A validation source alone does not establish success. When required validation has no supplied result, mark completeness unresolved rather than complete.

If rules conflict, preserve the conflict and leave requiredness unresolved unless precedence is supplied. Evaluate each request using only its type and applicable rules. With incomplete inputs, return a partial specification and explicit gaps. Use the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

Return JSON matching the [domain output schema](references/output-schema.json). The [synthetic shape example](references/schema-example.json) is illustrative, not executed evidence.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
