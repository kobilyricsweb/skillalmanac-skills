---
name: infrastructure-as-code-review
description: Reviews Terraform/OpenTofu, CloudFormation and Kubernetes files and plans. Use when the user says review my terraform, is this plan safe to apply, check these k8s manifests or this CloudFormation template. Finds open security groups, IAM wildcards, unencrypted or public storage, hard-coded secrets, missing retention and deletion protection, missing tags, `latest` images and missing memory limits, reads a plan for destroy and replace, and ranks changes with a risk table and a read-only JSON scanner. Do not use for general application code review, writing new infrastructure from scratch, running apply or destroy, or live cloud audits.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only, no network. Without Python, follow the checklists in step 3 and the plan procedure in step 4 by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Infrastructure-as-code review

Review infrastructure files as a change to production, not as code style. The reader of your report decides whether to merge or apply, so each finding must say what breaks or what it costs, at which file and line, and what to change. You read and recommend; you never run `apply`, `destroy`, `kubectl apply`, state commands or cloud CLIs against live systems.

## Workflow

```
- [ ] 1 Scope: which files, which cloud, which environment (prod or not)
- [ ] 2 Run the scanner on the files
- [ ] 3 Read each resource class against the checklist
- [ ] 4 If a plan or diff exists, read it with the plan procedure
- [ ] 5 Rank and verify findings
- [ ] 6 Report in the fixed shape
```

1. **Scope.** List the files in the change (a diff, a directory, or pasted text; save pasted text to files so the script can read it). Ask only what you cannot see: is this production, and does it hold data. Without an answer, assume yes for anything stateful.
2. **Scan.** `python scripts/iac_scan.py scan <paths>` (see Scripts). Every finding is a question to answer from the file, not a verdict. Without Python, work from step 3 alone.
3. **Checklist by resource class.** Open the file and look at each resource for the points below. The scanner covers many of them; the ones it cannot see (marked "by eye") are why you read the file.
   - **Network exposure.** Ingress from `0.0.0.0/0` or `::/0` (critical on 22, 3389 and database or cache ports; low on 80/443 only); public database flag; public IPs; Kubernetes `LoadBalancer` Services without source ranges; host network or host path. By eye: a rule whose CIDR is a variable that defaults to open.
   - **IAM.** `Action: "*"`, `service:*`, `Resource: "*"` on write actions, `Principal: "*"` without a Condition, AdministratorAccess, wildcard RBAC verbs, `cluster-admin` bindings. By eye: `iam:PassRole` or `sts:AssumeRole` on `*`, which is privilege escalation even without an Action wildcard.
   - **Storage.** Encryption off or unset; public ACL or public-access-block off; versioning off on buckets that hold records (by eye); a log or backup bucket with no lifecycle rule (by eye).
   - **Lifecycle and retention.** Log groups without `retention_in_days`; backup retention 0 or unset; `skip_final_snapshot`; no deletion protection; no `prevent_destroy`; `force_destroy`; CloudFormation stateful resources without both `DeletionPolicy` and `UpdateReplacePolicy`.
   - **Tags and owners.** Taggable resources with no tags and no provider default tags; tags with no owner or team key. Cost allocation and incident routing depend on these.
   - **Secrets.** Literal passwords, tokens, keys; Kubernetes `Secret` manifests and literal secret env vars; committed state files. By eye: secrets that reach state through `random_password` or a database `password` argument, which land in state in clear text unless the backend is protected.
   - **Supply chain.** Unpinned modules, `latest` or untagged images, floating Git refs.
   - **Kubernetes workloads.** No requests, no memory limit, no readiness probe, one replica, privileged or root containers.
4. **Plan or diff.** If the user supplied a plan, follow the plan procedure below. If not and the change touches stateful or network resources, say a plan is needed before approval and tell the user the commands to produce it (the user runs them).
5. **Rank and verify.** Order by the change-risk table. For each finding you keep, re-open the cited line and confirm it is real (variable defaults, `count = 0`, a module that sets the value, a Helm `{{ }}` template, a LimitRange). Drop or downgrade what you cannot confirm and say so.
6. **Report** in the shape at the end.

## Plan reading procedure

Full detail and symbols: [references/plan-reading.md](references/plan-reading.md). Read it when a plan, `kubectl diff` or change set is in the conversation.

1. Run `python scripts/iac_scan.py plan plan.json` when the user has a `terraform show -json` file; otherwise count `-`, `-/+`, `+/-` lines in the text plan by hand.
2. For every destroy or replace: name the resource, say whether it is stateful, quote the line that forces replacement, and state the data or address that is lost.
3. Check whether a destroy is really a rename (same type and similar arguments destroyed and created) or an index shift (`count` or list reordered). Both are fixed in code with `moved` blocks or `for_each`, not by applying.
4. List every `(known after apply)` and `(sensitive value)` that you could not review.
5. Never approve a plan with a destroy of a stateful resource unless the user states a backup exists and the destroy is intended.

## Change-risk table

Rank findings with this table. "Stateful" means data cannot be rebuilt by applying again.

| Change | Typical impact | Rank |
|---|---|---|
| Destroy or replace of a database, bucket, volume, file system, key or table | Data loss; hours of restore | Blocker |
| Ingress opened to the internet on admin or data ports; public bucket or database | Breach exposure | Blocker |
| Literal secret or key committed; state file committed | Credential leak; rotation | Blocker |
| IAM wildcard on write actions or public principal | Privilege escalation | High |
| Replace of VPC, subnet, load balancer, NAT gateway, elastic IP, certificate | Outage; address changes break allow-lists and DNS | High |
| Encryption turned on for an existing database or volume | Usually forces replacement; migration needed | High (plan it) |
| IAM role replaced | New unique id; trusts and caches break | Medium |
| Security group or policy narrowed on live traffic | Possible outage if a client was relying on it | Medium |
| No retention on logs; no backup retention; no deletion protection | Cost grows without bound; unrecoverable mistakes | Medium |
| Kubernetes: no memory limit, `latest` image, one replica, no probe | Node pressure, unreproducible rollouts, downtime on drain | Medium |
| Missing tags or owner; unpinned module | Cost attribution gaps; surprise upgrades | Low |
| Public IP on an instance that is meant to be public | Confirm intent | Low |

## Scripts

- `scripts/iac_scan.py scan <path> [<path> ...] [--fail-on LEVEL]`: run it; read-only. Walks directories (skips `.git` and `.terraform`), reads `.tf`, `.yaml`, `.yml`, `.json` up to 2 MB. Prints one strict JSON object: `tool`, `version`, `command`, `fail_on`, `files_scanned`, `files_skipped` (path, reason), `suppressed`, `summary` (counts of critical, high, medium, low, total), `findings` (each with `file`, `line`, `severity`, `rule`, `message`), `gate` (`pass` or `fail`) and `limits`. Exit 0 when no finding is at or above `--fail-on` (default `high`; `none` disables), 1 when the gate fails, 2 for a bad path or no readable files. A comment `iac-scan: ignore RULE-ID` on the same or previous line suppresses one finding; use it only with the owner's reason, and report suppressions.
- `scripts/iac_scan.py plan <plan.json> [--fail-on LEVEL]`: run it on `terraform show -json` output. Prints counts of create, update, delete, replace, no_op, read, `drift_count`, and a sorted `risky` list (`address`, `type`, `actions`, `action_reason`, `replace_paths`, `severity`, `why`). Exit codes as above; 2 when the file is not a plan.

Rule ids, detection and fixes: [references/rule-catalog.md](references/rule-catalog.md); read the row for any rule you report and the fix column when you propose a change. Sources and unconfirmed vendor claims: [references/sources.md](references/sources.md). Do not edit the script to make a check pass.

## Report shape

```
Verdict: <block | fix before merge | ok with notes>, with one line of why
Blockers: <file:line, rule, what breaks, fix as a corrected fragment or exact field change>
High / Medium / Low: <same shape, grouped>
Plan: <destroys and replaces with stateful flag, or "no plan supplied: needed because ...">
Suppressed or assumed: <ignored findings, assumptions about environment, unverified defaults marked verify>
Not checked: <live account state, module internals, variable values, Helm or Kustomize output>
```

Keep each finding to one or two lines of explanation, then give the fix as the corrected code: for Terraform, CloudFormation and Kubernetes findings, show the exact fragment to paste (for example the `valueFrom.secretKeyRef` block, a `resources:` block with requests and a memory limit, a pinned `image:` line, a `retention_in_days` line) or, at minimum, the exact field and value to set. A prose-only fix such as "add limits" is not enough. Group fixes for one resource into a single fragment. Mark values you had to guess (names, sizes, health paths) as placeholders to confirm. Do not list rules that did not fire. Do not pad with general best practice.

## Limits

- The scanner is regexes plus brace and indent counting, not an HCL or YAML parser. It does not resolve variables, locals, modules, `for_each`, dynamic blocks, Helm templates or Kustomize overlays, and it does not read CloudFormation JSON structure beyond line rules.
- Missing-attribute findings can be false positives when defaults come from a module, provider default tags, an account setting, a LimitRange or an admission policy. Provider defaults flagged verify (unconfirmed) were not checked against the user's provider version.
- It sees files, not the live account or cluster: drift, existing resources and real traffic are unknown.
- Severity from the plan command uses resource type names only.
- No findings means the patterns were not seen, not that the change is safe.
- Not a compliance audit and not a substitute for a security review of IAM design.
