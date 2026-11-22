# threat-model-stride-worksheet

## One line

Turns a described feature (assets, actors, trust boundaries, data flows) into a STRIDE threat table with 1 to 3 likelihood and impact scores, mitigations, owner roles and residual risk.

## What it does

The skill walks each data flow of a feature through the six STRIDE categories: spoofing, tampering, repudiation, information disclosure, denial of service and elevation of privilege. For every flow it either records a threat or records a "none" entry with a stated reason, so no category is silently skipped. Each threat receives a likelihood value and an impact value on a 1 to 3 scale, a score from 1 to 9, and a priority band. High-priority threats must carry a concrete mitigation and an owner role. After mitigation the threat is scored again to give a residual value. The output is a fixed set of sections: scope, threat table, coverage check, open items and a limits line. The worksheet lists threats and mitigations for a feature. It does not decide whether the feature is secure, and it does not write attack steps.

## When to use

Use it when a feature that handles logins, password resets, payment tokens or personal data is about to be built or changed, and the team needs a written threat model before the design is approved. It also suits a review of a proposed flow that has not been implemented yet, because the input is a description and not code.

## When not to use

Do not use it to certify a system as secure or compliant. Do not use it for penetration testing, exploit development or live-system probing. It does not review existing source code, configuration or logs. It is not a substitute for a security engineer's sign-off on High residual items.

## Requirements

A text-capable agent. No scripts, no network access and no additional files. The user must supply the feature purpose, assets, actors, trust boundaries and numbered data flows. Owners are recorded as roles, so the user should know which team or role will own each mitigation.

## Example

Excerpt from the smoke worksheet for a password reset by email, produced by following SKILL.md (full output is in VERIFICATION.md):

```
## Threat table
ID | Flow | STRIDE | Threat | L | I | Score | Priority | Mitigation | Owner role | Residual L | Residual I | Residual priority
T-F3-S | F3 | S | Attacker with a guessed or leaked token sets a new password | 2 | 3 | 6 | High | single-use token, 256 random bits, expires after 30 minutes (working value), stored as SHA-256 hash | Identity team lead | 1 | 3 | Medium
T-F1-I | F1 | I | Response differs for registered and unregistered emails (account enumeration) | 3 | 2 | 6 | High | same text and status for every email; response time padded to 500 ms (working value) | Web application lead | 2 | 1 | Low
```

## Limits

The scale values and score bands are working values chosen for this worksheet, not an industry standard. Scores depend entirely on the flows the user describes, so a missing flow means a missing threat. The worksheet does not model insider threats beyond the likelihood scale, does not test whether a mitigation works, and does not cover third-party provider internals.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
