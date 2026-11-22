# Listing page content: infrastructure-as-code-review

**One line:** Reviews Terraform, CloudFormation and Kubernetes files and plans for outage and bill risks, with a read-only JSON scanner.

## What it does

The skill gives an agent a six-step review: scope the change, run a scanner, read each resource class against a checklist (network exposure, IAM, storage, lifecycle and retention, tags, secrets, supply chain, Kubernetes workloads), read any plan or diff for destroy and replace, rank findings with a change-risk table, and report in a fixed shape that includes what was not checked. The scanner (`scripts/iac_scan.py`) uses regex rules plus brace and indentation counting, not a parser, and prints strict JSON with file, line, severity and rule for each finding. A second command classifies a `terraform show -json` plan by resource class so that a replaced database or a re-indexed subnet cannot hide in a long plan.

## Capabilities

- `iac_scan.py scan`: about 45 rule ids across Terraform/OpenTofu, CloudFormation YAML, Kubernetes YAML and JSON, with a pass or fail gate and a `--fail-on` threshold
- Content-based secret checks (AWS key ids, PEM headers, token shapes, literal secret-named attributes) and a committed-state-file check
- `iac_scan.py plan`: counts of create, update, delete, replace, a sorted risky list with `action_reason` and `replace_paths`
- A change-risk table, a rule catalog with a fix per rule, and a plan-reading guide for text plans, `kubectl diff` and CloudFormation change sets
- Vendor-dependent claims (provider defaults, per-type CloudFormation defaults, reason strings) marked "verify (unconfirmed)"

## When to use

You say review my terraform, is this plan safe to apply, check these k8s manifests, or look over this CloudFormation template, and the files or a plan are in the conversation.

## When not to use

General application code review (use a general code-review skill), writing new infrastructure from nothing, running `apply` or `destroy`, converting between formats, or auditing a live cloud account. How it differs from `reviewing-code-changes`: that skill reviews source diffs for broken callers, weak tests and unsafe migrations; this one knows infrastructure resource classes, plan symbols and what a replacement destroys.

## Requirements

Python 3.9 or newer for the script (standard library only). No network, no subprocess. Without Python the agent follows the checklist and plan procedure by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from the saved fixture run (`evals/fixtures/RESULTS.txt`, 12 of 12 cases pass), not from an agent session; no with-skill agent run exists yet.

1. `python scripts/iac_scan.py scan evals/files/t3-k8s` on a Deployment and a Service: summary 1 high, 3 medium, 2 low; findings `6 K8S-SINGLE-REPLICA`, `16 K8S-NO-RESOURCES`, `16 K8S-NO-READINESS`, `17 K8S-IMAGE-LATEST`, `22 K8S-ENV-SECRET` (the literal `STRIPE_API_KEY`), `29 K8S-PUBLIC-LB`; exit code 1 because of the high finding.
2. `python scripts/iac_scan.py plan evals/files/t2-plan/plan.json`: counts create 1, update 1, delete 1, replace 1, no_op 1; risky list `aws_db_instance.orders` critical (replace of a stateful resource, `replace_paths` is `storage_encrypted`) and `aws_subnet.private[0]` high (delete with reason `delete_because_count_index`); exit code 1.

## Limits

No HCL or YAML parser; variables, modules, `for_each`, dynamic blocks, Helm and Kustomize are not resolved. Missing-attribute findings can be false positives when defaults come from a module, provider default tags or an account setting. It reads files and plans, not the live account. No findings does not mean safe. Plan severity uses resource type names only.

## Evidence

Static lint and the fixture run only; see `VERIFICATION.md`. Not tested: with-skill against baseline, trigger rates, native discovery, cross-tool runs, human review.

## Demo script (60 to 90 seconds)

1. Prompt: "Is this plan safe to apply? We only wanted to turn on encryption and add a log group." Attach `plan.json`.
2. The agent runs the plan command; the terminal shows the database as a critical replace and a subnet destroy nobody asked for.
3. The agent explains: encryption forces the database to be recreated, and the subnet destroy comes from an index change; it asks for a backup confirmation and proposes a `moved` block.
4. Before: "looks fine, 1 to add". After: a ranked list of two blockers and what was not checked.

## FAQ seeds

1. Does it need network access? No. 2. Does it run `terraform` or `kubectl`? No; it reads files and plans you supply, and tells you which commands produce them. 3. Does it work with OpenTofu? The scanner reads the same `.tf` files; plan JSON compatibility is marked unconfirmed. 4. How is it different from `reviewing-code-changes`? See above. 5. Will it find every misconfiguration? No; it is regexes, not a parser, and lists its limits in each report. 6. Can I silence a finding? Yes, with an `iac-scan: ignore RULE-ID` comment; suppressions are counted in the output. 7. How do I uninstall? Delete the skill folder.

## Changelog

0.1.0, 2026-11-21: first draft; static lint and fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
