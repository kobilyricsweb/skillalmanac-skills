#!/usr/bin/env python3
"""Read-only scanner for infrastructure-as-code mistakes that cause outages and bills.

Usage:
    python iac_scan.py scan PATH [PATH ...] [--fail-on LEVEL]
    python iac_scan.py plan PLAN_JSON [--fail-on LEVEL]

scan   Reads .tf, .yaml, .yml and .json files (files or directories, recursive) and
       prints ONE strict JSON object: findings with file, line, severity, rule, message.
       Terraform/OpenTofu files get a brace-structure pass (blocks are found by counting
       braces, strings and heredocs are skipped). YAML files get an indentation pass for
       CloudFormation resources and Kubernetes documents. JSON files get the line rules
       only. This is NOT an HCL or YAML parser: see the "limits" array in the output.
plan   Reads the JSON made by `terraform show -json <planfile>` (OpenTofu: verify
       (unconfirmed) that the format is identical) and prints strict JSON: counts of
       create/update/delete/replace and a list of risky changes with severity.

Reads: the paths given. Writes: nothing (stdout only). No network, no subprocess.
Suppress one finding by putting `iac-scan: ignore RULE-ID` (or `ALL`) in a comment on the
same line or the line above; suppressed findings are counted, not listed.

Exit codes: 0 gate passed (no finding at or above --fail-on, default high);
            1 gate failed; 2 usage error or unreadable input.
"""
import argparse
import json
import os
import re
import sys

VERSION = "0.1.0"
SEVERITIES = ["low", "medium", "high", "critical"]
SEV_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}
SKIP_DIRS = {".git", ".terraform", ".terragrunt-cache", "node_modules", ".venv", "venv", "__pycache__"}
EXTS = (".tf", ".yaml", ".yml", ".json")
MAX_BYTES = 2000000  # larger files are skipped: generated state or lock files, not hand-written code
SUPPRESS_RE = re.compile(r"iac-scan:\s*ignore\s+([A-Za-z0-9_, -]+)")
Q = "[\"\x27]"  # a quote character, double or single

LIMITS = [
    "No HCL or YAML parser: rules are regexes plus brace/indent counting, so values built from "
    "variables, locals, modules, for_each, dynamic blocks, Helm templates or Kustomize overlays are not resolved.",
    "A missing-attribute finding may be a false positive when a module, provider default_tags, "
    "account-level setting, LimitRange or admission policy supplies the value.",
    "Absence of findings is not a clean bill of health; it only means these patterns were not seen.",
]

# Ports whose exposure to the whole internet is treated as critical: remote admin, databases, caches, Docker API.
CRITICAL_PORTS = {22, 23, 445, 1433, 1521, 2375, 3306, 3389, 5432, 5900, 6379, 9200, 11211, 27017}
WEB_PORTS = {80, 443}

# (rule, severity, regex, message, file extensions) applied line by line to comment-stripped text.
GENERIC = [
    ("IAM-WILDCARD-ACTION", "high",
     r"%s?\b(?:Action|actions)\b%s?\s*[:=]\s*(?:\[[^\]\n]*)?%s\*%s" % (Q, Q, Q, Q),
     "Action is a bare wildcard; list the exact actions (a Deny statement is the only safe use).",
     (".tf", ".yaml", ".yml", ".json")),
    ("IAM-WILDCARD-RESOURCE", "medium",
     r"%s?\bResource\b%s?\s*[:=]\s*(?:\[[^\]\n]*)?%s\*%s" % (Q, Q, Q, Q),
     "Resource is a bare wildcard; scope it to ARNs unless the action cannot be scoped.",
     (".tf", ".yaml", ".yml", ".json")),
    ("IAM-WILDCARD-RESOURCE", "medium",
     r"^\s*(?:resources|not_resources)\s*=\s*\[[^\]\n]*\"\*\"",
     "Policy resources contain a bare wildcard; scope it to ARNs unless the action cannot be scoped.",
     (".tf",)),
    ("IAM-SERVICE-WILDCARD", "medium", r"%s[a-z0-9-]{2,}:\*%s" % (Q, Q),
     "Service-wide action wildcard (service:*); name the actions that are needed.",
     (".tf", ".yaml", ".yml", ".json")),
    ("IAM-PUBLIC-PRINCIPAL", "high",
     r"%s?\bPrincipal\b%s?\s*[:=]\s*%s\*%s|%s?\bAWS\b%s?\s*[:=]\s*(?:\[\s*)?%s\*%s|\bidentifiers\s*=\s*\[\s*\"\*\"\s*\]"
     % (Q, Q, Q, Q, Q, Q, Q, Q),
     "Principal is everyone; safe only if a Condition limits the caller (check the same statement).",
     (".tf", ".yaml", ".yml", ".json")),
    ("IAM-ADMIN-POLICY", "high", r"arn:aws[\w-]*:iam::aws:policy/AdministratorAccess\b",
     "AdministratorAccess managed policy attached; grant a scoped policy instead.",
     (".tf", ".yaml", ".yml", ".json")),
    ("PUB-ACL", "critical", r"\bacl\s*=\s*\"public-read-write\"|\bAccessControl\s*:\s*%s?PublicReadWrite\b" % Q,
     "Bucket is world-writable.", (".tf", ".yaml", ".yml", ".json")),
    ("PUB-ACL", "high", r"\bacl\s*=\s*\"public-read\"|\bAccessControl\s*:\s*%s?PublicRead%s?\s*$" % (Q, Q),
     "Bucket ACL makes objects world-readable.", (".tf", ".yaml", ".yml", ".json")),
    ("PUB-ACCESS-BLOCK-OFF", "high",
     r"(?i)\b(?:block_public_acls|block_public_policy|ignore_public_acls|restrict_public_buckets)\s*=\s*false\b"
     r"|\b(?:BlockPublicAcls|BlockPublicPolicy|IgnorePublicAcls|RestrictPublicBuckets)\s*:\s*%s?false\b" % Q,
     "A public-access-block setting is turned off.", (".tf", ".yaml", ".yml", ".json")),
    ("PUB-DB", "high", r"(?i)\bpublicly_accessible\s*=\s*true\b|\bPubliclyAccessible\s*:\s*%s?true\b" % Q,
     "Database is reachable from the public internet.", (".tf", ".yaml", ".yml", ".json")),
    ("PUB-IP", "low",
     r"(?i)\b(?:associate_public_ip_address|map_public_ip_on_launch)\s*=\s*true\b"
     r"|\b(?:AssociatePublicIpAddress|MapPublicIpOnLaunch)\s*:\s*%s?true\b" % Q,
     "Public IP assigned automatically; confirm the instance is meant to be internet-facing.",
     (".tf", ".yaml", ".yml", ".json")),
    ("ENC-OFF", "high",
     r"(?i)\b(?:storage_encrypted|encrypted|transit_encryption_enabled|at_rest_encryption_enabled|enable_https_traffic_only)\s*=\s*false\b"
     r"|\b(?:StorageEncrypted|Encrypted)\s*:\s*%s?false\b" % Q,
     "Encryption is explicitly disabled.", (".tf", ".yaml", ".yml", ".json")),
    ("IMDS-OPTIONAL", "medium", r"\bhttp_tokens\s*=\s*\"optional\"|\bHttpTokens\s*:\s*%s?optional\b" % Q,
     "Instance metadata allows IMDSv1 (token optional); require tokens.", (".tf", ".yaml", ".yml", ".json")),
    ("LIFE-BACKUP-ZERO", "high", r"\bbackup_retention_period\s*=\s*0\b|\bBackupRetentionPeriod\s*:\s*%s?0%s?\s*$" % (Q, Q),
     "Automated backups are switched off (retention 0).", (".tf", ".yaml", ".yml", ".json")),
    ("LIFE-FINAL-SNAPSHOT-SKIP", "medium", r"\bskip_final_snapshot\s*=\s*true\b",
     "Destroying this database leaves no final snapshot.", (".tf",)),
    ("LIFE-DELETION-PROTECTION", "medium", r"\bdeletion_protection\s*=\s*false\b|\bDeletionProtection\s*:\s*%s?false\b" % Q,
     "Deletion protection is off for a stateful resource.", (".tf", ".yaml", ".yml", ".json")),
    ("LIFE-FORCE-DESTROY", "medium", r"\b(?:force_destroy|force_delete)\s*=\s*true\b",
     "Destroy will delete all contents (objects or images) without further prompt.", (".tf",)),
]
GENERIC = [(r, s, re.compile(p), m, e) for (r, s, p, m, e) in GENERIC]

SECRET_PATTERNS = [
    ("SEC-AWS-KEY", "critical", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "AWS access key id in source."),
    ("SEC-PRIVATE-KEY", "critical", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "Private key material in source."),
    ("SEC-TOKEN", "high",
     re.compile(r"\bsk-[A-Za-z0-9_-]{20,}|\bghp_[A-Za-z0-9]{36}\b|\bxox[baprs]-[A-Za-z0-9-]{10,}|\bAIza[0-9A-Za-z_-]{35}\b"),
     "Token-shaped string in source."),
]
SECRET_KEY_END = r"(?:password|passwd|secret|token|api_?key|access_?key|secret_?key|client_?secret|private_?key)"
LITERAL_QUOTED = re.compile(r"(?i)^\s*-?\s*%s?(?P<k>[A-Za-z0-9_.-]*%s)%s?\s*[:=]\s*(?P<q>[\"\x27])(?P<v>[^\"\x27]{4,})(?P=q)"
                            % (Q, SECRET_KEY_END, Q))
LITERAL_BARE = re.compile(r"(?i)^\s*-?\s*(?P<k>[A-Za-z0-9_.-]*%s)\s*:\s*(?P<v>[^\s\"\x27!{$#\[][^\s#]*)\s*$" % SECRET_KEY_END)
PLACEHOLDER = re.compile(r"(?i)^(<.*>|REPLACE.*|CHANGE_?ME|x{3,}|\*{3,}|\.{3}|true|false|null|none|\{\{.*\}\})$")


class Collector:
    """Gathers findings for one file, applying suppression comments and dropping duplicates."""

    def __init__(self, rel, raw):
        self.rel, self.raw, self.items, self.seen, self.suppressed = rel, raw, [], set(), 0

    def _is_suppressed(self, idx, rule):
        for j in (idx, idx - 1):
            if 0 <= j < len(self.raw):
                m = SUPPRESS_RE.search(self.raw[j])
                if m:
                    names = [x.strip().upper() for x in re.split(r"[,\s]+", m.group(1)) if x.strip()]
                    if "ALL" in names or rule in names:
                        return True
        return False

    def add(self, idx, severity, rule, message):
        key = (idx, rule)
        if key in self.seen:
            return
        self.seen.add(key)
        if self._is_suppressed(idx, rule):
            self.suppressed += 1
            return
        self.items.append({"file": self.rel, "line": idx + 1, "severity": severity, "rule": rule, "message": message})


def indent(s):
    return len(s) - len(s.lstrip(" "))


# ---------------------------------------------------------------- shared line rules

def secret_rules(col, raw, ext):
    for i, line in enumerate(raw):
        for rule, sev, rx, msg in SECRET_PATTERNS:
            if rx.search(line):
                col.add(i, sev, rule, msg)
        m = LITERAL_QUOTED.match(line)
        if not m and ext in (".yaml", ".yml"):
            m = LITERAL_BARE.match(line)
        if m:
            v = m.group("v").strip()
            if re.search(r"\$\{|\bvar\.|\blocal\.|\bdata\.|\bmodule\.|^arn:|^!|\{\{|^/|^https?://|^[a-z0-9_.-]+/[a-z0-9_.-]+$", v):
                continue
            if PLACEHOLDER.match(v):
                continue
            col.add(i, "high", "SEC-LITERAL",
                    "Literal value for secret-looking key '%s'; read it from a secret store or variable marked sensitive." % m.group("k"))


VAR_HEADER = re.compile(r"(?i)^\s*variable\s+\"([^\"]*%s)\"\s*\{" % SECRET_KEY_END)
VAR_DEFAULT = re.compile(r"^\s*default\s*=\s*\"(?P<v>[^\"]{4,})\"")


def variable_default_rules(col, code):
    """Terraform `variable` blocks whose name ends in a secret word and whose default is a literal."""
    i = 0
    while i < len(code):
        m = VAR_HEADER.match(code[i])
        if not m:
            i += 1
            continue
        name, depth, j = m.group(1), 0, i
        while j < len(code):
            line = code[j]
            if j > i:
                d = VAR_DEFAULT.match(line)
                if d and depth == 1:
                    v = d.group("v").strip()
                    if not re.search(r"\$\{|%\{", v) and not PLACEHOLDER.match(v):
                        col.add(j, "high", "SEC-LITERAL",
                                "Variable '%s' has a literal default that looks like a secret; a default is stored in source, so remove it and supply the value at run time (sensitive variable, secret manager)." % name)
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                break
            j += 1
        i = max(j, i) + 1


def generic_rules(col, code, ext):
    for i, line in enumerate(code):
        if not line.strip():
            continue
        for rule, sev, rx, msg, exts in GENERIC:
            if ext in exts and rx.search(line):
                col.add(i, sev, rule, msg)


def classify_ports(text):
    """Return (severity, description) for an internet-open rule from the ports named in `text`."""
    proto = re.search(r"(?i)\b(?:protocol|ip_protocol|IpProtocol)\b%s?\s*[:=]\s*%s?(-1|all)\b" % (Q, Q), text)
    if proto:
        return "critical", "all protocols and ports"
    ranges = []
    fp = re.search(r"(?i)\bfrom_?port\b%s?\s*[:=]\s*%s?(-?\d+)" % (Q, Q), text)
    tp = re.search(r"(?i)\bto_?port\b%s?\s*[:=]\s*%s?(-?\d+)" % (Q, Q), text)
    if fp and tp:
        ranges.append((int(fp.group(1)), int(tp.group(1))))
    pl = re.search(r"\bports\s*=\s*\[([^\]]*)\]", text)
    if pl:
        for tok in re.findall(r"(\d+)(?:-(\d+))?", pl.group(1)):
            ranges.append((int(tok[0]), int(tok[1] or tok[0])))
    dp = re.search(r"\bdestination_port_range\s*=\s*\"([^\"]*)\"", text)
    if dp:
        if dp.group(1) == "*":
            return "critical", "all ports"
        mm = re.match(r"(\d+)(?:-(\d+))?$", dp.group(1))
        if mm:
            ranges.append((int(mm.group(1)), int(mm.group(2) or mm.group(1))))
    if not ranges:
        return "high", "ports not determinable from this block"
    for lo, hi in ranges:
        if lo <= 0 and hi >= 65535:
            return "critical", "all ports"
    hit = sorted(p for p in CRITICAL_PORTS if any(lo <= p <= hi for lo, hi in ranges))
    if hit:
        return "critical", "port(s) %s" % ",".join(str(p) for p in hit)
    if all(lo in WEB_PORTS and hi in WEB_PORTS for lo, hi in ranges):
        return "low", "web port(s) only; confirm the service is meant to be public"
    return "high", "ports %s" % ",".join("%d-%d" % r if r[0] != r[1] else str(r[0]) for r in ranges)


# ---------------------------------------------------------------- Terraform / OpenTofu

STR_RE = re.compile(r"\"(?:[^\"\\]|\\.)*\"")
HEADER_RE = re.compile(r"^\s*([A-Za-z_][\w-]*)((?:\s+(?:\"[^\"]*\"|[A-Za-z_][\w-]*))*)\s*\{")
HEREDOC_RE = re.compile(r"<<-?\s*\"?([A-Za-z_]\w*)\"?\s*$")


class Block:
    def __init__(self, kind, labels, start, parent):
        self.kind, self.labels, self.start, self.end, self.parent = kind, labels, start, None, parent

    def name(self):
        return self.labels[0] if self.kind == "dynamic" and self.labels else self.kind


def strip_tf_comments(raw):
    out, in_block = [], False
    for ln in raw:
        if in_block:
            if "*/" in ln:
                ln = ln.split("*/", 1)[1]
                in_block = False
            else:
                out.append("")
                continue
        st = ln.lstrip()
        if st.startswith("/*"):
            if "*/" in st:
                ln = st.split("*/", 1)[1]
            else:
                in_block = True
                out.append("")
                continue
        st = ln.lstrip()
        out.append("" if st.startswith("#") or st.startswith("//") else ln)
    return out


def parse_blocks(code):
    blocks, stack, heredoc = [], [], None
    for i, ln in enumerate(code):
        if heredoc:
            if ln.strip() == heredoc:
                heredoc = None
            continue
        view = re.sub(r"\s#.*$", "", STR_RE.sub('""', ln))
        hm = HEADER_RE.match(ln)
        first = True
        for ch in view:
            if ch == "{":
                parent = next((b for b in reversed(stack) if b is not None), None)
                if hm and first:
                    labels = [a or b for a, b in re.findall(r"\"([^\"]*)\"|([A-Za-z_][\w-]*)", hm.group(2))]
                    blk = Block(hm.group(1), labels, i, parent)
                    blocks.append(blk)
                    stack.append(blk)
                else:
                    stack.append(None)
                first = False
            elif ch == "}" and stack:
                blk = stack.pop()
                if blk is not None:
                    blk.end = i
        hd = HEREDOC_RE.search(ln)
        if hd:
            heredoc = hd.group(1)
    for blk in blocks:
        if blk.end is None:
            blk.end = len(code) - 1
    return blocks


def btext(code, blk):
    return "\n".join(code[blk.start:blk.end + 1])


def has_attr(text, name):
    return re.search(r"(?m)^\s*%s\s*=" % re.escape(name), text) is not None


TF_TAGGABLE = {
    "aws_instance", "aws_s3_bucket", "aws_db_instance", "aws_rds_cluster", "aws_ebs_volume", "aws_lb", "aws_alb",
    "aws_vpc", "aws_subnet", "aws_security_group", "aws_dynamodb_table", "aws_lambda_function", "aws_sqs_queue",
    "aws_sns_topic", "aws_kms_key", "aws_eks_cluster", "aws_elasticache_cluster", "aws_efs_file_system",
    "aws_cloudwatch_log_group", "aws_nat_gateway", "aws_iam_role",
    "azurerm_resource_group", "azurerm_linux_virtual_machine", "azurerm_virtual_machine", "azurerm_storage_account",
    "azurerm_virtual_network", "azurerm_kubernetes_cluster", "azurerm_mssql_server",
    "google_compute_instance", "google_storage_bucket", "google_compute_disk",
}
TF_STATEFUL = {"aws_db_instance", "aws_rds_cluster", "aws_dynamodb_table", "aws_s3_bucket", "aws_efs_file_system", "aws_kms_key"}
OWNER_KEY = re.compile(r"(?i)\b(owner|team|squad|contact|cost[_-]?cent\w*)\b")


def tf_tags_map(code, blk):
    """Text of a literal `tags = { ... }` map inside a resource, or None when absent or non-literal."""
    for i in range(blk.start, blk.end + 1):
        if re.match(r"^\s*tags\s*=\s*\{", code[i]):
            ind = indent(code[i])
            if code[i].rstrip().endswith("}"):
                return code[i]
            out = [code[i]]
            for j in range(i + 1, blk.end + 1):
                out.append(code[j])
                if code[j].strip() == "}" and indent(code[j]) == ind:
                    break
            return "\n".join(out)
    return None


def scan_tf(col, raw, ctx):
    code = strip_tf_comments(raw)
    blocks = parse_blocks(code)
    if any(re.match(r"^\s*default_tags\s*\{", c) for c in code):
        ctx["default_tags"] = True
    # 1. open CIDR ingress
    for i, ln in enumerate(code):
        if "0.0.0.0/0" not in ln and "::/0" not in ln and not re.search(r"\"Internet\"|source_address_prefix\s*=\s*\"\*\"", ln):
            continue
        inner = None
        for b in blocks:
            if b.start <= i <= b.end and (inner is None or b.start >= inner.start):
                inner = b
        if inner is None:
            continue
        chain, cur = [], inner
        while cur is not None:
            chain.append(cur)
            cur = cur.parent
        res = next((b for b in chain if b.kind == "resource" and len(b.labels) >= 2), None)
        if res is None or not re.search(r"security_group|firewall|network_acl|network_security", res.labels[0]):
            continue
        text = btext(code, inner)
        if any(b.name() == "egress" for b in chain) or "egress" in res.labels[0] and "ingress" not in res.labels[0]:
            continue
        if re.search(r"(?i)\btype\s*=\s*\"egress\"|\bdirection\s*=\s*\"(?:EGRESS|Outbound)\"|\begress\s*=\s*true|\brule_action\s*=\s*\"deny\"|\baccess\s*=\s*\"Deny\"", text):
            continue
        sev, why = classify_ports(text)
        col.add(i, sev, "NET-OPEN-INGRESS", "Ingress open to the whole internet (%s); restrict the source to known CIDRs or a security group." % why)
    # 2. per-resource structure
    for b in blocks:
        if b.kind == "module" and b.parent is None:
            text = btext(code, b)
            m = re.search(r"(?m)^\s*source\s*=\s*\"([^\"]+)\"", text)
            if m and not m.group(1).startswith((".", "/")):
                src = m.group(1)
                git_like = src.startswith("git::") or "github.com" in src or "://" in src or src.startswith("git@")
                if git_like:
                    ref = re.search(r"[?&]ref=([^&\"]+)", src)
                    if not ref or ref.group(1) in ("main", "master", "HEAD", "develop"):
                        col.add(b.start, "medium", "SUP-MODULE-UNPINNED", "Module source has no immutable ref (tag or commit); a change upstream changes your plan.")
                elif not has_attr(text, "version"):
                    col.add(b.start, "medium", "SUP-MODULE-UNPINNED", "Registry module without a version constraint; pin a version.")
        if b.kind != "resource" or len(b.labels) < 2 or b.parent is not None:
            continue
        rtype, text = b.labels[0], btext(code, b)
        if rtype in ("aws_db_instance", "aws_rds_cluster"):
            if not has_attr(text, "storage_encrypted") and not has_attr(text, "replicate_source_db"):
                col.add(b.start, "medium", "ENC-MISSING", "storage_encrypted is not set (provider default is unencrypted: verify (unconfirmed) for your provider version).")
            if not has_attr(text, "deletion_protection"):
                col.add(b.start, "medium", "LIFE-DELETION-PROTECTION", "deletion_protection is not set (default is off).")
            if not has_attr(text, "backup_retention_period"):
                col.add(b.start, "low", "LIFE-RETENTION-MISSING", "backup_retention_period is not set; make the retention explicit (default: verify (unconfirmed)).")
        if rtype in ("aws_ebs_volume", "aws_efs_file_system") and not has_attr(text, "encrypted"):
            col.add(b.start, "medium", "ENC-MISSING", "encrypted is not set; an account-level default may cover it (verify).")
        if rtype == "aws_cloudwatch_log_group" and not has_attr(text, "retention_in_days"):
            col.add(b.start, "medium", "LIFE-RETENTION-MISSING", "retention_in_days is not set, so logs never expire and storage cost grows without bound.")
        if rtype in TF_STATEFUL and not re.search(r"prevent_destroy\s*=\s*true", text):
            col.add(b.start, "low", "LIFE-NO-PREVENT-DESTROY", "Stateful resource without lifecycle { prevent_destroy = true }.")
        if rtype == "aws_s3_bucket":
            ctx["buckets"].append((col, b.start, b.labels[1]))
        if rtype == "aws_s3_bucket_public_access_block":
            for mm in re.finditer(r"\bbucket\s*=\s*aws_s3_bucket\.(\w+)", text):
                ctx["pab"].add(mm.group(1))
        if rtype in TF_TAGGABLE:
            attr = "labels" if rtype.startswith("google_") else "tags"
            ctx["taggable"].append((col, b.start, rtype, has_attr(text, attr), tf_tags_map(code, b)))


# ---------------------------------------------------------------- YAML: CloudFormation + Kubernetes

CFN_STATEFUL = {"AWS::RDS::DBInstance", "AWS::RDS::DBCluster", "AWS::DynamoDB::Table", "AWS::S3::Bucket",
                "AWS::EFS::FileSystem", "AWS::EC2::Volume", "AWS::KMS::Key"}
CFN_TAGGABLE = CFN_STATEFUL | {"AWS::EC2::Instance", "AWS::EC2::SecurityGroup", "AWS::EC2::VPC", "AWS::EC2::Subnet",
                               "AWS::Lambda::Function", "AWS::SQS::Queue", "AWS::SNS::Topic", "AWS::ElasticLoadBalancingV2::LoadBalancer"}


def yaml_code(raw):
    return ["" if l.lstrip().startswith("#") or "{{" in l else l for l in raw]


def cfn_resources(code):
    out = []
    n = len(code)
    for i, ln in enumerate(code):
        m = re.match(r"^(\s*)Type:\s*[\"\x27]?(AWS::[\w:]+)", ln)
        if not m or not m.group(1):
            continue
        ind = len(m.group(1))
        j = i - 1
        while j >= 0 and (not code[j].strip() or indent(code[j]) >= ind):
            j -= 1
        if j < 0 or not re.match(r"^\s*[\w.-]+:\s*$", code[j]):
            continue
        k = j - 1
        while k >= 0 and (not code[k].strip() or indent(code[k]) >= indent(code[j])):
            k -= 1
        if k < 0 or not code[k].strip().startswith("Resources:"):
            continue
        end = i + 1
        while end < n and (not code[end].strip() or indent(code[end]) > indent(code[j])):
            end += 1
        out.append((j, end - 1, m.group(2)))
    return out


def yaml_item_window(code, idx):
    """Lines of the list item (or mapping) that contains line idx, found by indentation."""
    ind = indent(code[idx])
    s = idx
    while s > 0 and (not code[s - 1].strip() or indent(code[s - 1]) >= ind):
        s -= 1
    if s > 0 and code[s - 1].lstrip().startswith("-") and indent(code[s - 1]) < ind:
        s -= 1
    e = idx
    while e + 1 < len(code) and (not code[e + 1].strip() or indent(code[e + 1]) >= ind):
        e += 1
    return s, e


def scan_cfn(col, code):
    for s, e, rtype in cfn_resources(code):
        text = "\n".join(code[s:e + 1])

        def has(key):
            return re.search(r"(?m)^\s*-?\s*%s:" % key, text) is not None
        if rtype in ("AWS::RDS::DBInstance", "AWS::RDS::DBCluster"):
            if not has("StorageEncrypted"):
                col.add(s, "medium", "ENC-MISSING", "StorageEncrypted is not set (default is unencrypted: verify (unconfirmed)).")
            if not has("DeletionProtection"):
                col.add(s, "medium", "LIFE-DELETION-PROTECTION", "DeletionProtection is not set (default is off).")
        if rtype == "AWS::EC2::Volume" and not has("Encrypted"):
            col.add(s, "medium", "ENC-MISSING", "Encrypted is not set; an account-level default may cover it (verify).")
        if rtype == "AWS::Logs::LogGroup" and not has("RetentionInDays"):
            col.add(s, "medium", "LIFE-RETENTION-MISSING", "RetentionInDays is not set, so logs never expire.")
        if rtype == "AWS::S3::Bucket" and not has("PublicAccessBlockConfiguration"):
            col.add(s, "medium", "PUB-ACCESS-BLOCK-MISSING", "No PublicAccessBlockConfiguration on the bucket (an account-level block may cover it: verify).")
        if rtype in CFN_STATEFUL and not (has("DeletionPolicy") and has("UpdateReplacePolicy")):
            col.add(s, "medium", "LIFE-CFN-NO-POLICY",
                    "Stateful resource lacks DeletionPolicy and/or UpdateReplacePolicy; a delete or replacement removes the data (defaults per type: verify (unconfirmed)).")
        if rtype in CFN_TAGGABLE:
            if not has("Tags"):
                col.add(s, "low", "TAG-MISSING", "No Tags on a taggable resource (stack-level tags may cover it: verify).")
            elif not re.search(r"(?i)Key:\s*[\"\x27]?(owner|team|squad|contact|cost[_-]?cent\w*)", text):
                col.add(s, "low", "TAG-NO-OWNER", "Tags present but none names an owner, team or cost centre.")
    for i, ln in enumerate(code):
        if re.search(r"\bCidrIp:\s*[\"\x27]?0\.0\.0\.0/0|\bCidrIpv6:\s*[\"\x27]?::/0", ln):
            j = i - 1
            egress = False
            while j >= 0:
                if code[j].strip() and indent(code[j]) < indent(ln) and not code[j].lstrip().startswith("-"):
                    egress = "Egress" in code[j]
                    break
                j -= 1
            if egress:
                continue
            s, e = yaml_item_window(code, i)
            sev, why = classify_ports("\n".join(code[s:e + 1]))
            col.add(i, sev, "NET-OPEN-INGRESS", "Ingress open to the whole internet (%s); restrict the source CIDR or use a security group." % why)
    list_wildcards(col, code, cfn=True)


def list_wildcards(col, code, cfn=False, k8s=False):
    """Bare '*' list items: the owning key decides what the wildcard means."""
    for i, ln in enumerate(code):
        if not re.match(r"^\s*-\s*[\"\x27]\*[\"\x27]\s*$", ln):
            continue
        ind = indent(ln)
        j = i - 1
        while j >= 0 and (not code[j].strip() or (indent(code[j]) == ind and code[j].lstrip().startswith("-"))):
            j -= 1
        if j < 0:
            continue
        m = re.match(r"^\s*([\w:]+):\s*$", code[j])
        if not m:
            continue
        key = m.group(1)
        if cfn and key in ("Action", "Actions"):
            col.add(i, "high", "IAM-WILDCARD-ACTION", "Action is a bare wildcard; list the exact actions.")
        elif cfn and key == "Resource":
            col.add(i, "medium", "IAM-WILDCARD-RESOURCE", "Resource is a bare wildcard; scope it to ARNs.")
        elif cfn and key == "AWS":
            col.add(i, "high", "IAM-PUBLIC-PRINCIPAL", "Principal is everyone; safe only with a restricting Condition.")
        elif k8s and key == "verbs":
            col.add(i, "high", "K8S-RBAC-WILDCARD", "RBAC rule grants every verb; list the verbs needed.")
        elif k8s and key == "resources":
            col.add(i, "medium", "K8S-RBAC-WILDCARD", "RBAC rule covers every resource; list the resources needed.")


def k8s_docs(code):
    docs, start = [], 0
    for i, ln in enumerate(code + ["---"]):
        if ln.startswith("---"):
            docs.append((start, i))
            start = i + 1
    return docs


def container_items(code):
    n = len(code)
    for i, ln in enumerate(code):
        m = re.match(r"^(\s*)(containers|initContainers):\s*$", ln)
        if not m:
            continue
        kind, kind_ind = m.group(2), len(m.group(1))
        j = i + 1
        while j < n and not code[j].strip():
            j += 1
        if j >= n or not code[j].lstrip().startswith("-") or indent(code[j]) < kind_ind:
            continue
        ii, start, k, items = indent(code[j]), j, j + 1, []
        while k < n:
            if not code[k].strip():
                k += 1
                continue
            ind = indent(code[k])
            if ind < ii or (ind == ii and not code[k].lstrip().startswith("-")):
                break
            if ind == ii:
                items.append((start, k - 1))
                start = k
            k += 1
        items.append((start, k - 1))
        for s, e in items:
            yield kind, s, e


def image_problem(value):
    value = value.strip().strip("\"\x27")
    if not value or "$" in value or "{{" in value or "@sha256:" in value:
        return None
    last = value.rsplit("/", 1)[-1]
    if ":" not in last:
        return "has no tag, so it resolves to latest"
    if last.rsplit(":", 1)[1] == "latest":
        return "uses the latest tag"
    return None


def scan_container(col, code, kind, s, e, workload):
    lines = []
    for j in range(s, e + 1):
        ln = code[j]
        if j == s:
            m = re.match(r"^(\s*)-(\s+)(.*)$", ln)
            lines.append((j, len(m.group(1)) + 1 + len(m.group(2)), m.group(3)) if m else (j, indent(ln), ln.strip()))
        else:
            lines.append((j, indent(ln), ln.strip()))
    ci = lines[0][1]
    keys = {}
    for j, ind, txt in lines:
        m = re.match(r"^([\w-]+):\s*(.*)$", txt)
        if m and ind == ci and m.group(1) not in keys:
            keys[m.group(1)] = (j, m.group(2))
    if "image" in keys:
        prob = image_problem(keys["image"][1])
        if prob:
            col.add(keys["image"][0], "medium", "K8S-IMAGE-LATEST", "Image %s; pin a version tag or a digest so rollouts and rollbacks are reproducible." % prob)
    res = keys.get("resources")
    if res is None or res[1].strip() == "{}":
        col.add(s, "medium", "K8S-NO-RESOURCES", "Container has no resources block: no requests for the scheduler and no limits to contain it.")
    else:
        sections, cur, si = {}, None, None
        for j, ind, txt in lines:
            if j <= res[0] or ind <= ci:
                continue
            if si is None:
                si = ind
            m = re.match(r"^([\w.-]+):\s*(.*)$", txt)
            if not m:
                continue
            if ind == si:
                cur = m.group(1)
                sections[cur] = set(re.findall(r"([\w./-]+)\s*:", m.group(2)))
            elif cur is not None and ind > si:
                sections[cur].add(m.group(1))
        if inline_resources(res[1], sections):
            pass
        if "memory" not in sections.get("limits", set()):
            col.add(res[0], "medium", "K8S-NO-MEMORY-LIMIT", "No memory limit: one leak can take the node's memory (CPU limits are optional, memory limits are not).")
        if "requests" not in sections:
            col.add(res[0], "low", "K8S-NO-REQUESTS", "No resource requests: scheduling and autoscaling cannot reason about this container.")
    if workload and kind == "containers" and "readinessProbe" not in keys:
        col.add(s, "low", "K8S-NO-READINESS", "No readinessProbe: traffic is sent before the container is ready.")


def inline_resources(value, sections):
    """Handle `resources: {limits: {memory: 1Gi}}` written on one line."""
    m = re.search(r"limits\s*:\s*\{([^}]*)\}", value)
    if m:
        sections["limits"] = set(re.findall(r"([\w./-]+)\s*:", m.group(1)))
    m = re.search(r"requests\s*:\s*\{([^}]*)\}", value)
    if m:
        sections["requests"] = set(re.findall(r"([\w./-]+)\s*:", m.group(1)))
    return bool(value.strip())


def scan_k8s_doc(col, code, a, b):
    seg = code[a:b]
    kind = None
    has_api = False
    for ln in seg:
        if re.match(r"^apiVersion:", ln):
            has_api = True
        m = re.match(r"^kind:\s*[\"\x27]?(\w+)", ln)
        if m:
            kind = m.group(1)
    if not (has_api and kind):
        return False
    workload = kind in ("Deployment", "StatefulSet", "DaemonSet")
    for kk, s, e in container_items(code[a:b]):
        scan_container(_Offset(col, a), code[a:b], kk, s, e, workload)
    shift = _Offset(col, a)
    list_wildcards(shift, seg, k8s=True)
    for i, ln in enumerate(seg):
        if re.search(r"\bprivileged:\s*true\b", ln):
            shift.add(i, "high", "K8S-PRIVILEGED", "Privileged container: full host device access.")
        if re.search(r"\ballowPrivilegeEscalation:\s*true\b", ln):
            shift.add(i, "medium", "K8S-PRIVESC", "Container may gain more privileges than its parent process.")
        if re.search(r"\brunAsUser:\s*0\s*$", ln):
            shift.add(i, "medium", "K8S-RUN-AS-ROOT", "Container runs as UID 0.")
        if re.search(r"\b(?:hostNetwork|hostPID|hostIPC):\s*true\b", ln):
            shift.add(i, "high", "K8S-HOST-NAMESPACE", "Pod shares a host namespace (network, PID or IPC).")
        if re.match(r"^\s*-?\s*hostPath:\s*$", ln) or re.search(r"\bhostPath:\s*\{", ln):
            shift.add(i, "medium", "K8S-HOSTPATH", "hostPath volume exposes the node filesystem.")
        if re.search(r"\breadOnlyRootFilesystem:\s*false\b", ln):
            shift.add(i, "low", "K8S-WRITABLE-ROOTFS", "Root filesystem is writable.")
        if workload and kind != "DaemonSet" and re.match(r"^  replicas:\s*1\s*$", ln):
            shift.add(i, "low", "K8S-SINGLE-REPLICA", "Single replica: every rollout or node drain is an outage.")
        if re.search(r"^\s*name:\s*[\"\x27]?cluster-admin[\"\x27]?\s*$", ln):
            shift.add(i, "high", "K8S-CLUSTER-ADMIN", "Binding to cluster-admin; use a narrower role.")
        m = re.match(r"(?i)^\s*-\s*name:\s*[\"\x27]?(\w*%s)[\"\x27]?\s*$" % SECRET_KEY_END, ln)
        if m:
            nxt = i + 1
            while nxt < len(seg) and not seg[nxt].strip():
                nxt += 1
            if nxt < len(seg):
                vm = re.match(r"^\s*value:\s*[\"\x27]?([^\"\x27\s#][^\"\x27#]*)[\"\x27]?\s*$", seg[nxt])
                if vm and not PLACEHOLDER.match(vm.group(1).strip()):
                    shift.add(nxt, "high", "K8S-ENV-SECRET", "Secret-looking env var '%s' has a literal value; use secretKeyRef." % m.group(1))
    if kind == "Service":
        text = "\n".join(seg)
        if re.search(r"(?m)^  type:\s*LoadBalancer\s*$", text) and "loadBalancerSourceRanges" not in text and not re.search(r"(?i)internal|private", text):
            ln = next(i for i, x in enumerate(seg) if re.match(r"^  type:\s*LoadBalancer", x))
            shift.add(ln, "medium", "K8S-PUBLIC-LB", "LoadBalancer Service with no source ranges and no internal annotation is public on most clouds (annotation names differ per cloud: verify (unconfirmed)).")
    if kind == "Secret":
        for i, ln in enumerate(seg):
            if re.match(r"^(data|stringData):\s*$", ln):
                nxt = i + 1
                while nxt < len(seg) and not seg[nxt].strip():
                    nxt += 1
                if nxt < len(seg) and indent(seg[nxt]) > 0:
                    shift.add(i, "high", "K8S-SECRET-MANIFEST", "Secret values committed in a manifest; base64 is encoding, not encryption.")
    return True


class _Offset:
    """Collector view that shifts line indexes by the document start."""

    def __init__(self, col, off):
        self.col, self.off = col, off

    def add(self, idx, sev, rule, msg):
        self.col.add(idx + self.off, sev, rule, msg)


def scan_yaml(col, raw, ext):
    code = yaml_code(raw)
    generic_rules(col, code, ext)
    k8s_found = False
    for a, b in k8s_docs(code):
        if scan_k8s_doc(col, code, a, b):
            k8s_found = True
    if any(re.match(r"^\s*Type:\s*[\"\x27]?AWS::", l) for l in code):
        scan_cfn(col, code)
    return k8s_found


def scan_json(col, raw):
    text = "\n".join(raw)
    if '"terraform_version"' in text and '"serial"' in text and '"resources"' in text:
        col.add(0, "high", "STATE-COMMITTED", "Looks like a Terraform state file; state holds secrets in clear text and must not live in the repository.")


# ---------------------------------------------------------------- driver for `scan`

def collect_files(paths):
    files, skipped = [], []
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for nm in sorted(names):
                    if nm.lower().endswith(EXTS):
                        full = os.path.join(root, nm)
                        files.append((full, os.path.relpath(full, p).replace("\\", "/")))
        elif os.path.isfile(p):
            files.append((p, os.path.basename(p)))
        else:
            skipped.append({"path": p.replace("\\", "/"), "reason": "path does not exist"})
    return files, skipped


def run_scan(paths, fail_on):
    files, skipped = collect_files(paths)
    ctx = {"buckets": [], "pab": set(), "taggable": [], "default_tags": False}
    cols, suppressed, scanned = [], 0, 0
    for full, rel in files:
        try:
            if os.path.getsize(full) > MAX_BYTES:
                skipped.append({"path": rel, "reason": "larger than %d bytes" % MAX_BYTES})
                continue
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                raw = fh.read().splitlines()
        except OSError as exc:
            skipped.append({"path": rel, "reason": "unreadable: %s" % exc.__class__.__name__})
            continue
        ext = os.path.splitext(full)[1].lower()
        col = Collector(rel, raw)
        scanned += 1
        secret_rules(col, raw, ext)
        if ext == ".tf":
            code = strip_tf_comments(raw)
            generic_rules(col, code, ext)
            variable_default_rules(col, code)
            scan_tf(col, raw, ctx)
        elif ext in (".yaml", ".yml"):
            scan_yaml(col, raw, ext)
        else:
            generic_rules(col, ["" if l.lstrip().startswith(("#", "//")) else l for l in raw], ext)
            scan_json(col, raw)
        cols.append(col)
    for col, idx, name in ctx["buckets"]:
        if name not in ctx["pab"]:
            col.add(idx, "medium", "PUB-ACCESS-BLOCK-MISSING",
                    "No aws_s3_bucket_public_access_block references this bucket in the scanned files (a module or account-level block may cover it: verify).")
    for col, idx, rtype, has_tag_attr, tag_map in ctx["taggable"]:
        if not has_tag_attr and not (ctx["default_tags"] and rtype.startswith("aws_")):
            col.add(idx, "low", "TAG-MISSING", "No tags/labels on a taggable resource and no provider default_tags seen in the scanned files.")
        elif tag_map is not None and not OWNER_KEY.search(tag_map) and not re.search(r"merge\(|\blocal\.|\bvar\.|\.\.\.", tag_map):
            col.add(idx, "low", "TAG-NO-OWNER", "Tags present but none names an owner, team or cost centre.")
    findings = []
    for col in cols:
        findings.extend(col.items)
        suppressed += col.suppressed
    findings.sort(key=lambda f: (f["file"], f["line"], -SEV_RANK[f["severity"]], f["rule"]))
    summary = {s: sum(1 for f in findings if f["severity"] == s) for s in reversed(SEVERITIES)}
    summary["total"] = len(findings)
    gate = "pass"
    if fail_on != "none" and any(SEV_RANK[f["severity"]] >= SEV_RANK[fail_on] for f in findings):
        gate = "fail"
    return {"tool": "iac_scan", "version": VERSION, "command": "scan", "fail_on": fail_on, "files_scanned": scanned,
            "files_skipped": skipped, "suppressed": suppressed, "summary": summary, "findings": findings,
            "gate": gate, "limits": LIMITS}


# ---------------------------------------------------------------- `plan`

# Substrings of a resource type that hold data, names or addresses that cannot be rebuilt by re-applying.
STATEFUL_HINTS = ("db_instance", "rds_cluster", "db_cluster", "s3_bucket", "dynamodb_table", "efs_file_system", "kms_key",
                  "ebs_volume", "elasticache", "redshift", "opensearch", "elasticsearch_domain", "sql_database", "storage_account",
                  "docdb", "neptune", "msk_cluster", "secretsmanager_secret", "ecr_repository", "cosmosdb", "storage_bucket",
                  "bigquery_dataset", "spanner", "bigtable")
NETWORK_HINTS = ("aws_vpc", "_subnet", "route53_zone", "aws_lb", "aws_alb", "nat_gateway", "aws_eip", "internet_gateway",
                 "transit_gateway", "cloudfront_distribution", "acm_certificate", "route_table", "vpn_")
IDENTITY_HINTS = ("iam_role", "iam_user", "kms_alias", "service_account")
EXPOSURE_HINTS = ("security_group", "network_acl", "firewall", "iam_policy", "iam_role_policy", "bucket_policy",
                  "public_access_block", "kms_key_policy")
# severity by (change kind, resource class)
PLAN_SEVERITY = {
    "replace": {"stateful": "critical", "network": "high", "identity": "medium", "other": "medium"},
    "delete": {"stateful": "critical", "network": "high", "identity": "medium", "other": "low"},
}


def resource_class(rtype):
    for name, hints in (("stateful", STATEFUL_HINTS), ("network", NETWORK_HINTS), ("identity", IDENTITY_HINTS)):
        if any(h in rtype for h in hints):
            return name
    return "other"


def run_plan(path, fail_on):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, "cannot read %s as JSON (%s)" % (path, exc.__class__.__name__)
    if not isinstance(data, dict) or "resource_changes" not in data:
        return None, "no resource_changes key: produce the input with `terraform show -json <planfile>`"
    counts = {"create": 0, "update": 0, "delete": 0, "replace": 0, "no_op": 0, "read": 0}
    risky = []
    for rc in data["resource_changes"]:
        change = rc.get("change", {})
        acts = change.get("actions", [])
        aset = set(acts)
        if aset == {"no-op"}:
            counts["no_op"] += 1
            continue
        if aset == {"read"}:
            counts["read"] += 1
            continue
        if "delete" in aset and "create" in aset:
            kind = "replace"
        elif aset == {"delete"}:
            kind = "delete"
        elif aset == {"create"}:
            kind = "create"
        else:
            kind = "update"
        counts[kind] += 1
        rtype = rc.get("type", "")
        item = {"address": rc.get("address"), "type": rtype, "actions": acts, "action_reason": rc.get("action_reason"),
                "replace_paths": change.get("replace_paths")}
        if kind in PLAN_SEVERITY:
            cls = resource_class(rtype)
            item["severity"] = PLAN_SEVERITY[kind][cls]
            item["why"] = "%s of a resource in the %s class%s" % (kind, cls, " (create-before-destroy order)" if acts[:1] == ["create"] else "")
            risky.append(item)
        elif kind == "update" and any(h in rtype for h in EXPOSURE_HINTS):
            item["severity"] = "medium"
            item["why"] = "in-place change to a permission or exposure resource: read the before/after values"
            risky.append(item)
    risky.sort(key=lambda r: (-SEV_RANK[r["severity"]], r["address"] or ""))
    summary = {s: sum(1 for r in risky if r["severity"] == s) for s in reversed(SEVERITIES)}
    gate = "pass"
    if fail_on != "none" and any(SEV_RANK[r["severity"]] >= SEV_RANK[fail_on] for r in risky):
        gate = "fail"
    return {"tool": "iac_scan", "version": VERSION, "command": "plan", "fail_on": fail_on, "counts": counts,
            "drift_count": len(data.get("resource_drift", [])), "summary": summary, "risky": risky, "gate": gate,
            "limits": ["Severity comes from the resource type name only; it cannot see data volume, dependencies or traffic.",
                       "In-place updates are not listed unless the type is a permission or exposure resource; read the plan for the rest."]}, None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="iac_scan.py", description="Read-only IaC risk scanner (strict JSON on stdout).")
    sub = ap.add_subparsers(dest="command")
    sc = sub.add_parser("scan", help="scan .tf/.yaml/.yml/.json files or directories")
    sc.add_argument("paths", nargs="+")
    pl = sub.add_parser("plan", help="classify a `terraform show -json` plan")
    pl.add_argument("plan_json")
    for p in (sc, pl):
        p.add_argument("--fail-on", default="high", choices=SEVERITIES + ["none"], help="lowest severity that fails the gate (default high)")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if args.command is None:
        ap.print_usage(sys.stderr)
        return 2
    if args.command == "scan":
        report = run_scan(args.paths, args.fail_on)
        if report["files_scanned"] == 0:
            sys.stderr.write("error: no .tf/.yaml/.yml/.json files were read from the given paths\n")
            return 2
    else:
        report, err = run_plan(args.plan_json, args.fail_on)
        if err:
            sys.stderr.write("error: %s\n" % err)
            return 2
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=False) + "\n")
    return 1 if report["gate"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
