Synthetic input:
Inventory en: title = “Welcome”.
Inventory fr: no title key.
Inventory es: no title key.
Fallback rule: fr falls back to en.
No fallback rule is supplied for es.
Terminal policy: not supplied.

Actual artifact:

| Requested locale | Key | Status | Source locale | Path | Notes |
|---|---|---|---|---|---|
| fr | title | inherited | en | fr → en | en supplies title |
| es | title | unresolved | — | es | no fallback edge supplied |
| en | title | local | en | en | local value supplied |

The Spanish result remains unresolved; the input does not authorize an arbitrary English fallback. No conclusion is made about missing-key display behavior because the terminal policy is absent.
