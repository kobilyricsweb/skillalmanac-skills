---
name: compose-to-kubernetes-mapping
description: Maps the services of a Docker Compose file to Kubernetes Deployment, Service and PersistentVolumeClaim skeletons, with one row per Compose key and a gap list for every key that does not translate. Use when a user asks to convert docker compose to kubernetes, or needs to know which Compose keys have no Kubernetes equivalent. Do not use for writing Helm charts, cluster sizing, image builds, or applying manifests to a live cluster.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Compose to Kubernetes mapping

Maps one Docker Compose file to Kubernetes skeletons. Each key under each service gets one row with a target field or NO-EQUIVALENT, and every gap is listed.

## Intake

Required: the full text of one Compose file with a top-level `services:` mapping.
Optional: target namespace, names of Secrets already created, storage size per named volume, image name for each `build` service.
A missing optional fact keeps its placeholder, sets Status to partial, and goes under Open questions.

Stop rule: if the Compose text is missing, is not a mapping, or has no `services:` key, map nothing. Return `Status: blocked` and a numbered question list naming each missing required fact. A file longer than 300 lines (working value) is also blocked; ask the user to split it by service.

## Workflow

1. Intake check. Output: Status (continue, partial, or blocked). Ignore a top-level `version:` key. Read top-level `volumes:` only to see which named volumes are declared. `networks:` produces no rows.
2. Inventory services in file order. Output: the service count and each service name.
3. List the keys directly under each service. Each key is one row. Output: the key list per service.
4. Map each key with the decision table below. Output: one row per key.
5. Apply the Ports table and the environment rule to the `ports` and `environment` rows.
6. Apply the Volume table to the `volumes` row.
7. Build the skeletons using only the allowed fields in the skeleton rules. Output: YAML blocks.
8. Count rows and list gap items. Output: the Counts table and the Gap list.
9. Set the status and write Open questions. Output: the Status line and the questions.

### Decision table

A row's status is the worst status among its sub-items, in the order NO-EQUIVALENT > PARTIAL > MAPPED.

| Compose key | Kubernetes target | Status |
|---|---|---|
| image | containers[0].image | MAPPED |
| entrypoint | containers[0].command | MAPPED |
| command | containers[0].args | MAPPED |
| working_dir | containers[0].workingDir | MAPPED |
| environment | containers[0].env | MAPPED, or PARTIAL when rule 5 applies |
| ports | Service ports and containers[0].ports | per Ports table |
| expose | containers[0].ports, containerPort only | PARTIAL (no Service port) |
| volumes | PersistentVolumeClaim and volumeMounts | per Volume table |
| deploy (replicas, resources.limits only) | spec.replicas, containers[0].resources.limits | MAPPED |
| deploy (any other subkey) | none | NO-EQUIVALENT |
| labels | metadata.labels | MAPPED |
| user (numeric) | securityContext.runAsUser | MAPPED |
| user (name) | none | PARTIAL |
| privileged | securityContext.privileged | MAPPED |
| read_only | securityContext.readOnlyRootFilesystem | MAPPED |
| cap_add | securityContext.capabilities.add | MAPPED |
| restart | none (Deployment restart policy is always) | PARTIAL |
| env_file | none (file contents are not read) | PARTIAL |
| build | none | NO-EQUIVALENT |
| depends_on | none (no start order field) | NO-EQUIVALENT |
| healthcheck | none (write probes by hand) | NO-EQUIVALENT |
| networks | none | NO-EQUIVALENT |
| logging | none | NO-EQUIVALENT |
| container_name | none (Pod names are generated) | NO-EQUIVALENT |
| tty, stdin_open | none | NO-EQUIVALENT |
| any other key | none | NO-EQUIVALENT, note "unrecognized key" |

### Ports table

| Compose form | Example | Container port | Service port | Status |
|---|---|---|---|---|
| container only | "80" | 80 | none | PARTIAL (no host port) |
| host:container | "8080:80" | 80 | 8080 | MAPPED |
| ip:host:container | "127.0.0.1:8080:80" | 80 | 8080, host IP dropped | PARTIAL |
| with protocol | "53:53/udp" | 53 | 53, protocol UDP | MAPPED |
| range | "8000-8010:8000-8010" | not expanded | none | PARTIAL |

A `/tcp` suffix or no suffix emits no protocol field.

### Environment rule

1. A name containing PASSWORD, PASS, SECRET, TOKEN, KEY, or CREDENTIAL (case-insensitive) is a secret. So is a value containing `://` followed later by `@`. These are working values; the owner sets the final list.
2. A secret becomes `valueFrom.secretKeyRef` with name `<service>-secrets` and key equal to the variable name. Its value is written as `<redacted>` everywhere, including the Value column.
3. A literal value is copied as written.
4. A value written as `${NAME}` is not resolved. Use `<value-required>`.
5. Any secret or `${NAME}` value makes the environment row PARTIAL.

The list form `- NAME=value` is read as NAME with that value; `- NAME` with no value is `<value-required>` and makes the row PARTIAL. The same secret test applies to NAME.

### Volume table

| Compose form | Example | Kubernetes | Status |
|---|---|---|---|
| named, declared at top level | app-data:/var/lib/app | PVC app-data and volumeMount | PARTIAL |
| named, not declared at top level | cache:/tmp/cache | PVC cache and volumeMount, plus an Open question | PARTIAL |
| named, read-only | app-data:/data:ro | as named, volumeMount readOnly true | PARTIAL |
| bind (starts with ./, ../, /, or ~) | ./src:/app | none | NO-EQUIVALENT |
| anonymous (container path only) | /data | none | NO-EQUIVALENT |

A Docker socket path (`/var/run/docker.sock`) adds "host access" to its gap reason. A named volume mounted by two or more services keeps `<access-mode-required>`, which produces an Open question.

## Skeleton rules

- Derived values allowed: metadata.name and container name equal the service name; selector and Pod labels `app: <service>`; secretKeyRef name `<service>-secrets`; PVC name equals the volume name.
- Deployment: always emitted. `spec.replicas` only when `deploy.replicas` exists in the file.
- Image: the `image` value, else `<image-required>`.
- Service: emitted only when at least one port has a host port. It lists only those ports.
- PersistentVolumeClaim: one per named volume, emitted once even when shared. Storage size is `<size-required>`; access mode is `<access-mode-required>`.
- Never add replicas, probes, resource limits, image tags, or credentials that the file does not state.

## Counting and status

- Services: count of service entries.
- Service keys read: total rows across all service tables.
- MAPPED, PARTIAL, NO-EQUIVALENT: row counts. Their sum equals Service keys read.
- Gap items: PARTIAL plus NO-EQUIVALENT rows. Each gap item is one row in the Gap list.
- Status `complete`: no Open questions.
- Status `partial`: one or more Open questions, a refused clause, or a missing optional fact.
- Status `blocked`: the intake stop rule fired. Output only the Status line and the question list.

## Refuse or stop when

- Intake is missing or has no `services:` mapping: blocked, with the question list.
- The file is longer than 300 lines (working value): blocked, ask for a split by service.
- A request asks to invent an image name, resource limit, replica count, or credential: refuse that clause only, keep the placeholder, set partial, list the refused item under Open questions.
- A request asks to write a secret value into the output: refuse that clause, write `<redacted>`, set partial.
- A request asks for Helm charts, cluster sizing, image builds, or applying manifests: refuse that clause only, map the file anyway, set partial.

## Output contract

```
# Compose to Kubernetes mapping: <project name or unnamed>
Status: complete | partial | blocked

## Counts
| Metric | Value |        (rows: Services, Service keys read, MAPPED, PARTIAL, NO-EQUIVALENT, Gap items)

## Service mapping
### <service name>        (one heading per service, file order)
| Compose key | Value in file | Kubernetes target | Status | Note |

## Skeleton
One Deployment YAML block per service, then Service where it applies, then one PersistentVolumeClaim block per named volume.

## Gap list
| ID | Service | Compose key | Status | Reason |        (G1, G2 ... one row per PARTIAL or NO-EQUIVALENT row)

## Open questions        (only when Status is partial or blocked)
Numbered list: one question per placeholder, one per undeclared named volume.
```

Files in this package: [SKILL.md](SKILL.md) and [LICENSE.txt](LICENSE.txt).
