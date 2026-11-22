# terraform-resource-diagram

## One line

Turns the resource and data blocks in a Terraform folder into a Mermaid graph and lists references that point to nothing declared.

## What it does

The script reads one `.tf` file, or every `.tf` file directly inside one folder, and strips comments while keeping string literals. It then finds each `resource` and `data` header, matches the braces to find where the block ends, and searches the block body for references shaped like `type.name` or `data.type.name`. A reference counts only when the provider type contains an underscore, which keeps Terraform words such as `var`, `local`, `module`, and `each` out of the graph.

Every reference that matches a declared block becomes an arrow from the referencing block to the target. A reference with no matching declaration becomes a dashed edge to an "(unresolved)" node, and the run prints a U001 finding. The script also searches the graph for cycles, duplicate declarations, and inputs with no blocks at all. The diagram is printed to stdout as a `graph LR` block, with the findings written as Mermaid comment lines so the output stays valid Mermaid.

## When to use

Use it when someone has a folder of Terraform files and wants to see which resources depend on which before a refactor, a review, or an incident write-up. It is also useful for finding a reference to a resource that was renamed or removed from the scanned files.

## When not to use

Do not use it to validate Terraform, to run a plan, to read state, or to check provider schemas. It does not read `.tf.json`, modules fetched from a registry, or files outside the folder it is given. It cannot resolve a reference that lives in another module.

## Requirements

Python 3.9 or later, standard library only. No network access, no subprocess calls, and no write access to the inputs. The optional `--out` flag writes to a new file and refuses to overwrite.

## Example

Run on the smoke fixture, which is a five-block input with one unresolved reference. The fixture is stored as `fixtures/smoke/main.tf.txt` and was copied to a scratch folder as `main.tf` before the run.

```text
graph LR
%% U001 unresolved reference aws_kms_key.logs in aws_s3_bucket.logs
  n0["aws_vpc.main"]
  n1["aws_subnet.public"]
  n2["aws_security_group.web"]
  n3["aws_instance.app"]
  n4["aws_s3_bucket.logs"]
  u0["aws_kms_key.logs (unresolved)"]
  n1 --> n0
  n2 --> n0
  n3 --> n1
  n3 --> n2
  n4 -.-> u0
```

Exit code 1, because one finding was printed. The counts are 5 drawn nodes and 4 drawn resolved edges, plus one dashed unresolved edge.

## Limits

- The parser is regular-expression based. It is not an HCL parser, so interpolations with nested quotes, heredocs that contain a line starting with a `resource` header, and braces inside strings can confuse block matching.
- Reference detection needs an underscore in the provider type. A reference to a type with no underscore is not drawn.
- The script does not check whether a reference is valid for the provider, whether the attribute exists, or whether the code would plan or apply.
- The 2 MB input cap and the 150-node cap are working values, not limits published by Terraform.
- It does not check security settings, cost, drift, or whether the diagram matches what is deployed.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
