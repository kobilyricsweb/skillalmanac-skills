# Sources and what is unconfirmed

Written in the skill author's own words. The pages below were named from memory of their location and were not re-fetched while this skill was written; open them before relying on any detail marked verify.

| Topic | Where to confirm | What this skill uses it for |
|---|---|---|
| Terraform JSON plan format (resource_changes, actions, action_reason, resource_drift, replace_paths) | https://developer.hashicorp.com/terraform/internals/json-format | field names read by `iac_scan.py plan`; the list of reason strings is marked verify |
| Terraform lifecycle meta-arguments (prevent_destroy, create_before_destroy, ignore_changes) | https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle | the LIFE-NO-PREVENT-DESTROY advice and the create-before-destroy action order |
| Terraform moved blocks | https://developer.hashicorp.com/terraform/language/modules/develop/refactoring | advice to avoid destroy plus create when renaming |
| OpenTofu documentation | https://opentofu.org/docs/ | confirming the plan JSON is the same as Terraform's: not confirmed |
| CloudFormation DeletionPolicy and UpdateReplacePolicy | https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-attribute-deletionpolicy.html and https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-attribute-updatereplacepolicy.html | the claim that a replaced or deleted resource loses its data unless a policy retains it; per-type defaults are marked verify |
| CloudFormation change sets (Replacement field) | https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html | reading `Replacement` values |
| Kubernetes resource requests and limits | https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ | the memory-limit rule; the position that CPU limits are optional is a judgement, not a requirement |
| Kubernetes Pod Security Standards | https://kubernetes.io/docs/concepts/security/pod-security-standards/ | privileged, host namespace, hostPath and privilege-escalation rules |
| S3 Block Public Access | https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html | the four public-access-block flags |
| EC2 instance metadata (IMDSv2) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html | the http_tokens rule |

Unconfirmed claims in this skill, each marked "verify (unconfirmed)" where it appears: provider defaults for storage encryption, backup retention and deletion protection; CloudFormation default policies per resource type; whether OpenTofu's plan JSON is identical; the complete list of `action_reason` strings; exact version in which `moved` blocks and `resource_drift` appeared; per-cloud annotation names for internal load balancers; which attribute changes force replacement for a given provider version.
