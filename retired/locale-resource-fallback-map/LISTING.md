# locale-resource-fallback-map

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when supplied locale inventories and explicit fallback chains must be mapped to determine how resource keys resolve. Do not use for changing application resources, inventing fallback edges, or general localization writing without inventories and declared rules.

## Task boundary

configuration-key-drift-check validates config names; this resolves locale resource keys through explicitly declared fallback chains.

## Try the independent synthetic example

Create a locale resolution map. Inventories: fr-CA has {greet:“Allô”}; fr has {greet:“Bonjour”, bye:“Au revoir”}; root has {bye:“Bye”}. Declared ordered chains: fr-CA -> fr -> root; fr -> root. Terminal policy: return a missing-key marker when no supplied locale has the key; this policy does not create a value. Resolve fr-CA/greet, fr-CA/bye, and fr-CA/help. Preserve exact keys and do not edit resources.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_dc5600f07d72`:

```text
{"resolutions":[{"requested_locale":"fr-CA","key":"greet","status":"local","source_locale":"fr-CA","fallback_path":["fr-CA"],"value":"Allô","notes":"The requested locale supplies the key."},{"requested_locale":"fr-CA","key":"bye","status":"inherited","source_locale":"fr","fallback_path":["fr-CA","fr"],"value":"Au revoir","notes":"The key is found through the declared fallback chain."},{"requested_locale":"fr-CA","key":"help","status":"missing","source_locale":null,"fallback_path":["fr-CA","fr","root"],"value":null,"notes":"No supplied locale in the declared chain has this key; apply the missing-key marker policy."}],"missing_inputs":[],"rule_conflicts":[],"scope_note":"This map follows only the supplied chains and inventories; it does not edit resources or create values."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
