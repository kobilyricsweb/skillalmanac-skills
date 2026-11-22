## Contents

- How to read a rule row
- Network exposure
- Identity and access
- Storage encryption and public access
- Lifecycle, retention and deletion
- Tags and ownership
- Secrets and state
- Supply chain
- Kubernetes
- Fixes that are safe to propose

# Rule catalog for `scripts/iac_scan.py`

Every rule id the script can emit, how it detects the problem, and the fix to propose. "Line rule" means one regex on one comment-stripped line. "Block rule" means the script found the enclosing resource by counting braces (Terraform) or indentation (YAML) and looked at the whole block. Both kinds miss anything built from variables, modules or templates.

## How to read a rule row

Severity is the script's default. Raise it when the resource holds production data or sits in the path of customer traffic; lower it for sandboxes. A rule marked `verify` has a default that depends on provider, API or account version that this skill could not confirm: check the current provider or service documentation before telling the user it is a defect.

## Network exposure

| Rule | Kind | Detection | Severity | Fix |
|---|---|---|---|---|
| NET-OPEN-INGRESS | block | `0.0.0.0/0` or `::/0` inside an ingress block of a security group, firewall or network ACL resource; egress blocks and deny rules are skipped. Ports are read from from/to_port, `ports = [...]` or `destination_port_range`. | critical: all protocols or ports, or any of 22, 23, 445, 1433, 1521, 2375, 3306, 3389, 5432, 5900, 6379, 9200, 11211, 27017; high: any other port, or ports not readable from the block; low: only 80 and/or 443 | Source from a corporate CIDR, a VPN range, or another security group. Public web traffic belongs behind a load balancer whose own group is the only open one. |
| PUB-DB | line | `publicly_accessible = true`, `PubliclyAccessible: true` | high | Set false; reach the database through a private subnet, bastion or VPN. |
| PUB-IP | line | `associate_public_ip_address`, `map_public_ip_on_launch` true | low | Keep only where the instance is meant to be internet-facing. |
| K8S-PUBLIC-LB | block | Service `type: LoadBalancer` with no `loadBalancerSourceRanges` and no annotation containing "internal" or "private" | medium; annotation names differ by cloud: verify (unconfirmed) | Add the cloud's internal-load-balancer annotation or source ranges, or use an Ingress with an authenticated edge. |
| K8S-HOST-NAMESPACE | line | `hostNetwork`, `hostPID` or `hostIPC` true | high | Remove; use a Service or NodePort if a port must be reachable. |

## Identity and access

| Rule | Kind | Detection | Severity | Fix |
|---|---|---|---|---|
| IAM-WILDCARD-ACTION | line + list | `Action` or `actions` equal to a bare `*`, inline or as a YAML list item under an `Action:` key | high | Enumerate actions; if the job is "everything in a service", name the service and review the list. |
| IAM-WILDCARD-RESOURCE | line + list | `Resource` (or Terraform `resources`) containing a bare `*` | medium | Scope to ARNs. Some actions cannot be scoped (for example certain describe/list calls): say so and keep the wildcard only on those statements. |
| IAM-SERVICE-WILDCARD | line | a quoted `service:*` action | medium | Name the needed actions. |
| IAM-PUBLIC-PRINCIPAL | line | `Principal` = `*`, `AWS` = `*`, or `identifiers = ["*"]` | high | Name accounts or roles; if truly public, require a Condition (source VPC endpoint, organization id) and say why. |
| IAM-ADMIN-POLICY | line | the AdministratorAccess managed policy ARN | high | Replace with a scoped policy. |
| K8S-RBAC-WILDCARD | list | `verbs` list containing `*` (high), `resources` list containing `*` (medium) | high / medium | Enumerate verbs and resources. |
| K8S-CLUSTER-ADMIN | line | a `name: cluster-admin` line (role reference) | high | Bind a narrower ClusterRole or a namespaced Role. |
| K8S-PRIVILEGED / K8S-PRIVESC / K8S-RUN-AS-ROOT | line | `privileged: true`; `allowPrivilegeEscalation: true`; `runAsUser: 0` | high / medium / medium | Drop to the needed capability only; run as a non-zero UID. |
| K8S-HOSTPATH / K8S-WRITABLE-ROOTFS | line | `hostPath` volume; `readOnlyRootFilesystem: false` | medium / low | Use a PVC or emptyDir; mount a writable tmp volume and make the root read-only. |
| IMDS-OPTIONAL | line | `http_tokens = "optional"` or `HttpTokens: optional` | medium | Require tokens (`required`). Check old agents that may still use IMDSv1 first. |

## Storage encryption and public access

| Rule | Kind | Detection | Severity | Fix |
|---|---|---|---|---|
| ENC-OFF | line | `storage_encrypted`, `encrypted`, `transit_encryption_enabled`, `at_rest_encryption_enabled`, `enable_https_traffic_only` set to false; CloudFormation `StorageEncrypted`/`Encrypted` false | high | Set true. Changing it on an existing volume or database usually forces replacement: read the plan (see plan-reading.md). |
| ENC-MISSING | block | RDS instance or cluster without `storage_encrypted` (read replicas excluded); EBS volume or EFS file system without `encrypted`; CloudFormation equivalents | medium; verify (unconfirmed) the default for your provider version and any account-level default | Set it explicitly and plan the replacement. |
| PUB-ACL | line | `acl = "public-read"` (high) or `"public-read-write"` (critical); CloudFormation `AccessControl: PublicRead(Write)` | high / critical | Remove the ACL; serve public content through a CDN with origin access control. |
| PUB-ACCESS-BLOCK-OFF | line | any of the four public-access-block flags set false | high | Set true, or document the exception in a comment. |
| PUB-ACCESS-BLOCK-MISSING | cross-file | a bucket resource name that no `aws_s3_bucket_public_access_block` references in the scanned files; CloudFormation bucket without `PublicAccessBlockConfiguration` | medium; may be covered at account or module level: verify | Add the block resource. |

## Lifecycle, retention and deletion

| Rule | Kind | Detection | Severity | Fix |
|---|---|---|---|---|
| LIFE-RETENTION-MISSING | block | log group without `retention_in_days` / `RetentionInDays` (medium: logs never expire); database without `backup_retention_period` (low; default verify (unconfirmed)) | medium / low | Set a number of days that matches policy. |
| LIFE-BACKUP-ZERO | line | backup retention 0 | high | Set at least 7 for production, per policy. |
| LIFE-FINAL-SNAPSHOT-SKIP | line | `skip_final_snapshot = true` | medium | Set false and name a final snapshot identifier. |
| LIFE-DELETION-PROTECTION | line + block | `deletion_protection = false` or the attribute missing on a database | medium | Set true for anything with data; turn it off deliberately before an intended destroy. |
| LIFE-FORCE-DESTROY | line | `force_destroy` or `force_delete` true | medium | Leave false on anything that holds data; enable only for scratch buckets. |
| LIFE-NO-PREVENT-DESTROY | block | stateful Terraform type without `prevent_destroy = true` | low | Add the lifecycle block on databases, buckets, tables, file systems and keys. |
| LIFE-CFN-NO-POLICY | block | stateful CloudFormation resource missing `DeletionPolicy` or `UpdateReplacePolicy` | medium; per-type defaults: verify (unconfirmed) | Set `Retain` or `Snapshot` where supported on both attributes. |
| K8S-SINGLE-REPLICA | line | Deployment or StatefulSet with `replicas: 1` at the spec level | low | Run at least two with a PodDisruptionBudget if the service must survive node drains. |

## Tags and ownership

| Rule | Kind | Detection | Severity | Fix |
|---|---|---|---|---|
| TAG-MISSING | block + cross-file | taggable resource without `tags` (`labels` for Google types); skipped for AWS types when any scanned file has a provider `default_tags` block | low | Add tags or provider default tags. |
| TAG-NO-OWNER | block | a literal tags map with no key named owner, team, squad, contact or cost-centre; skipped when the map uses merge(), var., local. or a spread | low | Add an owner key with a team address, and a cost-centre key if billing is split. |

## Secrets and state

| Rule | Kind | Detection | Severity | Fix |
|---|---|---|---|---|
| SEC-AWS-KEY | line, raw file text including comments | `AKIA` or `ASIA` followed by 16 upper-case letters or digits | critical | Revoke the key now; history keeps it. |
| SEC-PRIVATE-KEY | line | a PEM private-key header | critical | Revoke and rotate; move to a secret store. |
| SEC-TOKEN | line | `sk-` + 20 or more token characters, GitHub `ghp_` tokens, Slack `xox` tokens, Google `AIza` keys | high | Revoke and rotate. |
| SEC-LITERAL | line | a key whose name ENDS in password, passwd, secret, token, api_key, access_key, secret_key, client_secret or private_key, with a quoted literal of 4 or more characters; YAML also matches an unquoted literal. Skipped when the value contains an interpolation, var., local., data., module., a template, an ARN or URL, or is a placeholder such as REPLACE_ME, CHANGE_ME or xxx | high | Use a sensitive variable, a secret manager data source, or a secretKeyRef. Also fires on the `default = "literal"` line of a Terraform `variable` block whose name ends in one of those words (same skips; empty defaults are not flagged); `sensitive = true` does not excuse a literal default. |
| K8S-ENV-SECRET | block | env entry whose name ends like a secret key and whose next line is a literal `value:` | high | Use `valueFrom.secretKeyRef`. |
| K8S-SECRET-MANIFEST | block | `kind: Secret` with `data` or `stringData` entries | high | Use an external secret operator or sealed secrets; base64 is not protection. |
| STATE-COMMITTED | file content | a JSON file containing `terraform_version`, `serial` and `resources` keys | high | Remove from the repo, move state to a remote backend with encryption and locking, rotate every secret that was in it. |

## Supply chain

| Rule | Kind | Detection | Severity | Fix |
|---|---|---|---|---|
| SUP-MODULE-UNPINNED | block | registry module without `version`; git module without `ref=`, or with `ref=main`, `master`, `HEAD` or `develop` | medium | Pin a version or a tag/commit. |
| K8S-IMAGE-LATEST | line | image with tag `latest` or with no tag (digest-pinned images pass) | medium | Pin a version tag; prefer a digest for production. |

## Kubernetes

| Rule | Kind | Detection | Severity | Fix |
|---|---|---|---|---|
| K8S-NO-RESOURCES | block | container with no `resources` or `resources: {}` | medium | Add requests and a memory limit. |
| K8S-NO-MEMORY-LIMIT | block | `resources` present but `limits.memory` missing | medium | Set a memory limit near the observed peak plus headroom. CPU limits are a judgement call (throttling), memory limits are not. |
| K8S-NO-REQUESTS | block | `resources` present but no `requests` | low | Add requests so the scheduler and autoscaler have data. |
| K8S-NO-READINESS | block | Deployment, StatefulSet or DaemonSet container with no `readinessProbe` (init containers excluded) | low | Add a probe that checks real readiness, not just that the port is open. |

## Fixes that are safe to propose

Safe to write directly: adding tags, retention days, `prevent_destroy`, `deletion_protection`, version pins, memory limits, readiness probes, removing a wildcard that the policy visibly does not need. Propose but do not apply without the owner: anything that changes encryption on an existing stateful resource, narrows a security group or IAM policy that live traffic uses, switches an image tag in a running workload, or moves a secret. Those can cause replacement or an outage; follow the risk table in SKILL.md.
