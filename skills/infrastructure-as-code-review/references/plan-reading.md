## Contents

- Getting a plan you can read
- Reading the text plan
- Reading the JSON plan
- Replacement triggers worth knowing
- Kubernetes and CloudFormation equivalents
- Questions to ask before approving

# Reading plans and diffs

## Getting a plan you can read

Ask the user to produce a saved plan so that what is reviewed is what is applied: `terraform plan -out=tfplan`, then `terraform show tfplan` for text and `terraform show -json tfplan > plan.json` for the machine form (OpenTofu uses `tofu` in place of `terraform`; verify (unconfirmed) that its JSON is field-for-field identical). The agent never runs `apply`, `destroy` or `state` commands for the user; it reads a plan the user supplies. If only a text plan exists, use the next section by hand.

## Reading the text plan

Symbols at the start of a resource line:

| Marker | Meaning | Review stance |
|---|---|---|
| `+` | create | Check cost, naming collisions and what it attaches to. |
| `~` | update in place | Read each changed attribute; some "in place" changes still interrupt service (instance type, parameter groups needing reboot: verify per service). |
| `-` | destroy | Stop: what data or address goes away, and is the removal intended (resource removed from code, or a `count`/`for_each` key that changed)? |
| `-/+` | destroy then create (replace) | Stop: the old one is deleted before the new one exists unless `create_before_destroy` is set. |
| `+/-` | create then destroy | Replacement with the new resource created first; names and unique constraints may collide. |
| `<=` | data source read | No change, but may fail or be unknown. |

Search the text for the phrase `forces replacement`. The attribute line carrying it is the cause; show it to the user. A plan that ends with a count of "to destroy" above zero is never a rubber-stamp, even when the destroyed item looks like a rename.

Values marked `(known after apply)` cannot be reviewed now; list them as unverified. Values marked `(sensitive value)` are hidden: ask for confirmation that they did not change unexpectedly.

A moved or renamed resource shows as destroy plus create unless a `moved` block or `terraform state mv` was used (moved blocks need Terraform 1.1 or later: verify). Before accepting that pair for a stateful resource, ask for a `moved` block.

## Reading the JSON plan

Top-level keys the script uses: `resource_changes` (list) and, when present, `resource_drift` (resources that changed outside Terraform since the last apply; presence depends on version: verify (unconfirmed)). Per resource change: `address`, `type`, `mode` (managed or data), `change.actions`, optionally `action_reason`, `change.replace_paths`.

`change.actions` values: `["no-op"]`, `["read"]`, `["create"]`, `["update"]`, `["delete"]`, `["delete","create"]` (replace), `["create","delete"]` (replace with create-before-destroy order). Reason strings seen in documentation include `replace_because_cannot_update`, `replace_because_tainted`, `replace_by_request`, `delete_because_no_resource_config`, `delete_because_wrong_repetition` and `delete_because_count_index` / `delete_because_each_key`; the full and current list: verify (unconfirmed) in the format documentation. The script prints the value as given and never depends on it.

Interpretation of reasons: `delete_because_no_resource_config` means someone removed the resource block or the module call that held it; `delete_because_*count*` / `*each*` means an index disappeared from a list or map, which is how re-ordering a list silently destroys the wrong item. `replace_because_cannot_update` means the changed attribute is immutable for that resource type.

`python scripts/iac_scan.py plan plan.json` turns this into counts and a risky list sorted by severity. Treat its list as the minimum to discuss, not the full review: it knows resource type names, not data size.

## Replacement triggers worth knowing

These are typical, per provider documentation; confirm in the plan itself because versions differ (verify (unconfirmed) each for the provider version in use).

- Database: changing the engine, identifier, encryption flag or availability zone on an existing instance can force replacement, with data loss unless a snapshot restore is planned.
- Volumes and file systems: switching encryption or availability zone replaces the volume.
- Network: changing the CIDR block of a VPC or subnet replaces it and everything attached to it; changing a name prefix on a security group that is in use can fail or replace and re-attach.
- Load balancer, NAT gateway, elastic IP: replacement changes the address that DNS, allow-lists and partners depend on.
- Role: replacing an IAM role changes its unique id; trust policies and resources that cached it can break even though the name is the same.
- Count to for_each (or the reverse), or reordering a list used with `count`: every address changes, so the plan shows destroy plus create for resources that did not really change. Fix with `moved` blocks or by keying with `for_each`.

## Kubernetes and CloudFormation equivalents

- Kubernetes: ask for `kubectl diff -f <manifests>` output (read-only against the cluster; the user runs it). Changes to a Deployment's pod template restart pods; changes to immutable fields (a Service's clusterIP, a Deployment's selector, a StatefulSet's volumeClaimTemplates) are rejected or require delete and recreate. A removed manifest is only deleted with pruning; check how the pipeline applies.
- CloudFormation: ask for a change set (`aws cloudformation create-change-set`, then describe it; the user runs it). The `Replacement` field per resource is `True`, `False` or `Conditional`; treat `Conditional` as True until proven otherwise. On replacement the old resource is removed after the new one is created, and is deleted for good unless `UpdateReplacePolicy` is `Retain` or `Snapshot`.

## Questions to ask before approving

1. Does any `-`, `-/+` or `+/-` line touch a stateful resource? If yes: is there a backup newer than the change, and has a restore been tried?
2. Does any address change for a resource that did not change? That is a rename or index problem, not a real destroy.
3. What is in `(known after apply)` that the next resource depends on?
4. Does the plan include drift the author did not expect? Someone changed production by hand; applying overwrites it.
5. Is the plan file the one that will be applied, and how old is it?
