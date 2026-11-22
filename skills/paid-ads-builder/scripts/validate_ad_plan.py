#!/usr/bin/env python3
"""Validate a paid-ads plan stored as JSON. Strict JSON report on stdout.

Usage:
    python scripts/validate_ad_plan.py plan.json
    python scripts/validate_ad_plan.py plan.json --strict   # warnings also fail

Reads: the plan file only. Writes: nothing. No network. Standard library only.
Exit codes: 0 no errors (warnings allowed unless --strict), 1 at least one
error, 2 the file is missing, unreadable or not a JSON object.

The plan shape is documented in SKILL.md. Every finding has a severity
("error" or "warning"), a stable code, a JSON-path-like location and a message
that says what to fix. Do not edit this script to make a plan pass; fix the
plan, or use the plan's own "limit_overrides" when a platform limit has changed.
"""
import argparse
import json
import re
import sys


def split_url(url):
    """Return (scheme, host, query dict of first values). Minimal, no dependencies."""
    m = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*)://([^/?#]*)([^?#]*)(?:\?([^#]*))?(?:#.*)?$", url.strip())
    if not m:
        return "", "", {}
    query = {}
    for part in (m.group(4) or "").split("&"):
        if part:
            key, _, val = part.partition("=")
            query.setdefault(key, val)
    return m.group(1).lower(), m.group(2), query

# Character limits per platform and field. kind "hard" = the platform rejects
# or cuts the text (error); "display" = only the visible part is cut (warning).
# Every number here is "verify (unconfirmed, as of 2026-11)": platforms change
# limits, so a plan may override any value with "limit_overrides".
LIMITS = {
    "google_search": {"headline": (30, "hard"), "description": (90, "hard"), "path": (15, "hard")},
    "microsoft_search": {"headline": (30, "hard"), "description": (90, "hard"), "path": (15, "hard")},
    "meta": {"primary_text": (125, "display"), "headline": (40, "display"), "description": (30, "display")},
    "linkedin": {"primary_text": (150, "display"), "headline": (70, "display"), "description": (100, "display")},
    "tiktok": {"primary_text": (100, "hard")},
}
SEARCH_PLATFORMS = ("google_search", "microsoft_search")
# Responsive search ad asset counts (verify, unconfirmed, as of 2026-11).
RSA_HEADLINES = (3, 15)
RSA_DESCRIPTIONS = (2, 4)
REQUIRED_UTM = ("utm_source", "utm_medium", "utm_campaign")
# Below this many expected conversions per campaign per month, automated bid
# strategies tend to learn slowly. Rule of thumb, not a platform rule.
MIN_CONVERSIONS_FOR_AUTOMATED_BIDDING = 30
AUTOMATED_BIDS = ("max_conversions", "target_cpa", "target_roas", "max_conversion_value")
# Relative tolerance when comparing a declared figure with a recomputed one,
# wide enough for rounding of cpc and cvr, narrow enough to catch a slip.
REL_TOL = 0.02
ABS_TOL = 0.5
SPECIAL_VERTICALS = ("housing", "credit", "employment")
# Targeting keys that must not appear for special ad categories.
RESTRICTED_TARGETING = ("age_min", "age_max", "gender", "zip_codes", "postal_codes", "lookalike")

# (pattern, category, severity, why)
CLAIM_RULES = [
    (r"\bguarantee[sd]?\b", "absolute", "error", "guarantee claim needs written terms; most platforms reject it in ad text"),
    (r"\brisk[- ]free\b|\bno[- ]risk\b|\bzero risk\b", "absolute", "error", "risk-free claims are routinely disapproved"),
    (r"\bmiracle\b|\bcures?\b|\bcure[- ]all\b", "health", "error", "cure and miracle claims are prohibited in health ads"),
    (r"\b(lose|drop|shed)\s+\d+\s*(lbs?|pounds|kg|kilos)\b", "health", "error", "specific weight-loss outcomes are restricted"),
    (r"\bbefore (and|&) after\b", "health", "error", "before-and-after imagery or claims are restricted for health and weight loss"),
    (r"\byou (have|suffer from|are suffering from) (diabetes|depression|anxiety|cancer|debt|bad credit|a (disease|condition|disorder))\b", "personal_attribute", "error", "ad text must not imply knowledge of the viewer's condition or status"),
    (r"\bare you (diabetic|depressed|overweight|bankrupt|in debt|pregnant)\b", "personal_attribute", "error", "asking about a sensitive personal attribute implies you know it"),
    (r"\bguaranteed (returns?|profit|income|approval)\b|\bdouble your money\b|\bget rich\b|\bpassive income\b", "finance", "error", "income and return promises are restricted in finance ads"),
    (r"\b(no credit check|pre-?approved|instant approval|zero interest)\b", "finance", "error", "credit offers need disclosed terms; these phrases are a common cause of disapproval"),
    (r"\b(families|singles|couples|no kids|adults only|young professionals|christian|exclusive neighborhood)\b", "housing", "error", "housing and rental copy must not describe preferred occupants"),
    (r"\b(young|recent grads?|digital native|youthful)\b.*\b(wanted|hiring|needed)\b", "employment", "error", "job ads must not signal an age preference"),
    (r"\bfree (money|cash|gift)\b", "absolute", "warning", "free money and gift wording draws manual review"),
    (r"\b(best|#1|number one|top[- ]rated|leading)\b", "superlative", "warning", "superlatives need a verifiable source on the landing page"),
    (r"\bclick here\b", "style", "warning", "generic call to action; name the benefit instead"),
]
# Rule categories applied only when the plan's "vertical" matches, so that an
# ordinary "families" in a plumber's ad is not flagged.
VERTICAL_ONLY = {"housing": ("housing",), "employment": ("employment",)}


def add(findings, severity, code, path, message):
    findings.append({"severity": severity, "code": code, "path": path, "message": message})


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def close(declared, computed):
    return abs(declared - computed) <= max(ABS_TOL if computed < 50 else 0, REL_TOL * abs(computed))


def strip_kw(kw):
    return re.sub(r'^[\[\]"+\s-]+|[\[\]"\s]+$', "", kw.strip()).lower()


def get_limit(plan, platform, field):
    over = plan.get("limit_overrides", {})
    if isinstance(over, dict) and isinstance(over.get(platform), dict) and is_num(over[platform].get(field)):
        return int(over[platform][field]), LIMITS.get(platform, {}).get(field, (0, "hard"))[1]
    return LIMITS.get(platform, {}).get(field)


def check_copy_string(plan, findings, platform, field, text, path):
    if not isinstance(text, str):
        add(findings, "error", "copy_type", path, "copy must be a string")
        return
    lim = get_limit(plan, platform, "path" if field.startswith("path") else field)
    if lim and len(text) > lim[0]:
        add(findings, "error" if lim[1] == "hard" else "warning", "copy_over_limit", path,
            f"{len(text)} characters, limit {lim[0]} for {platform} {field} (verify, unconfirmed, as of 2026-11); shorten by {len(text) - lim[0]}")
    if not text.strip():
        add(findings, "error", "copy_empty", path, "empty copy")
    if platform in SEARCH_PLATFORMS and field == "headline" and "!" in text:
        add(findings, "error", "copy_exclamation", path, "search headlines may not contain an exclamation mark")
    if re.search(r"!{2,}|\?{2,}", text):
        add(findings, "warning", "copy_punctuation", path, "repeated punctuation is a common disapproval reason")
    words = re.findall(r"[A-Za-z]{4,}", text)
    if words and sum(1 for w in words if w.isupper()) >= 2:
        add(findings, "warning", "copy_all_caps", path, "two or more ALL-CAPS words; platforms treat this as shouting")
    for pattern, category, severity, why in CLAIM_RULES:
        if category in VERTICAL_ONLY and plan.get("vertical") not in VERTICAL_ONLY[category]:
            continue
        if re.search(pattern, text, re.IGNORECASE):
            add(findings, severity, "claim_" + category, path, f"'{text[:60]}': {why}")


def check_ad(plan, findings, platform, ad, path):
    if not isinstance(ad, dict):
        add(findings, "error", "ad_shape", path, "each ad must be an object")
        return
    if platform in SEARCH_PLATFORMS:
        heads, descs = ad.get("headlines"), ad.get("descriptions")
        if not isinstance(heads, list) or not isinstance(descs, list):
            add(findings, "error", "ad_shape", path, "search ads need 'headlines' and 'descriptions' lists")
            return
        if not RSA_HEADLINES[0] <= len(heads) <= RSA_HEADLINES[1]:
            add(findings, "error", "rsa_headline_count", path + ".headlines",
                f"{len(heads)} headlines, expected {RSA_HEADLINES[0]} to {RSA_HEADLINES[1]} (verify, unconfirmed, as of 2026-11)")
        if not RSA_DESCRIPTIONS[0] <= len(descs) <= RSA_DESCRIPTIONS[1]:
            add(findings, "error", "rsa_description_count", path + ".descriptions",
                f"{len(descs)} descriptions, expected {RSA_DESCRIPTIONS[0]} to {RSA_DESCRIPTIONS[1]} (verify, unconfirmed, as of 2026-11)")
        for i, h in enumerate(heads):
            check_copy_string(plan, findings, platform, "headline", h, f"{path}.headlines[{i}]")
        for i, d in enumerate(descs):
            check_copy_string(plan, findings, platform, "description", d, f"{path}.descriptions[{i}]")
        for key in ("path1", "path2"):
            if key in ad:
                check_copy_string(plan, findings, platform, key, ad[key], f"{path}.{key}")
        seen = set()
        for h in heads:
            if isinstance(h, str):
                k = h.strip().lower()
                if k in seen:
                    add(findings, "warning", "copy_duplicate", path + ".headlines", f"duplicate headline '{h}'")
                seen.add(k)
    else:
        any_field = False
        for field in ("primary_text", "headline", "description"):
            if field in ad:
                any_field = True
                check_copy_string(plan, findings, platform, field, ad[field], f"{path}.{field}")
        if not any_field:
            add(findings, "error", "ad_shape", path, "social ads need at least 'primary_text' or 'headline'")


def check_utm(findings, url, path):
    q = split_url(url)[2]
    out = {}
    for key in REQUIRED_UTM:
        val = q.get(key)
        if val is None or not val.strip():
            add(findings, "error", "utm_missing", path, f"{key} is missing or empty in {url}")
            continue
        out[key] = val
        if val != val.lower() or re.search(r"\s|%20|\+", val):
            add(findings, "error", "utm_format", path, f"{key}='{val}' must be lowercase with no spaces (analytics treats case variants as different values)")
    return out


def check_campaign(plan, findings, camp, ci, state):
    path = f"campaigns[{ci}]"
    platform = camp.get("platform")
    if platform not in LIMITS:
        add(findings, "error", "platform_unknown", path + ".platform", f"platform must be one of {sorted(LIMITS)}")
        return
    for key in ("objective", "audience"):
        if not camp.get(key):
            add(findings, "error", "campaign_missing_" + key, path, f"campaign has no {key}")
    # --- budget arithmetic
    daily, days, budget = camp.get("daily_budget"), camp.get("days"), camp.get("budget")
    if is_num(daily) and is_num(days) and is_num(budget):
        if abs(daily * days - budget) > 0.01:
            add(findings, "error", "budget_mismatch", path, f"daily_budget {daily} x days {days} = {round(daily * days, 2)}, but budget is {budget}")
    else:
        add(findings, "error", "budget_missing", path, "daily_budget, days and budget must all be numbers")
    if is_num(budget):
        state["budget_sum"] += budget
    fc = camp.get("forecast")
    bid = camp.get("bid_strategy", "")
    if isinstance(fc, dict) and is_num(budget) and is_num(fc.get("cpc")) and fc["cpc"] > 0 and is_num(fc.get("cvr")):
        clicks_calc = budget / fc["cpc"]
        if is_num(fc.get("clicks")) and not close(fc["clicks"], clicks_calc):
            add(findings, "error", "forecast_clicks_mismatch", path + ".forecast", f"budget {budget} / cpc {fc['cpc']} = {round(clicks_calc, 1)} clicks, plan says {fc['clicks']}")
        base_clicks = fc["clicks"] if is_num(fc.get("clicks")) else clicks_calc
        conv_calc = base_clicks * fc["cvr"]
        if is_num(fc.get("conversions")) and not close(fc["conversions"], conv_calc):
            add(findings, "error", "forecast_conversions_mismatch", path + ".forecast", f"clicks {round(base_clicks, 1)} x cvr {fc['cvr']} = {round(conv_calc, 1)} conversions, plan says {fc['conversions']}")
        conv = fc["conversions"] if is_num(fc.get("conversions")) else conv_calc
        if conv <= 0:
            add(findings, "error", "forecast_zero_conversions", path + ".forecast", "forecast produces no conversions; the campaign cannot meet any CPA target")
        else:
            cpa = budget / conv
            target = camp.get("target_cpa", plan.get("target_cpa"))
            if is_num(target) and cpa > target * (1 + REL_TOL):
                add(findings, "warning", "cpa_above_target", path + ".forecast", f"implied CPA {round(cpa, 2)} (budget / conversions) is above target_cpa {target}")
            if bid in AUTOMATED_BIDS and conv < MIN_CONVERSIONS_FOR_AUTOMATED_BIDDING:
                add(findings, "warning", "bid_learning_data_thin", path + ".bid_strategy", f"{round(conv, 1)} expected conversions is under {MIN_CONVERSIONS_FOR_AUTOMATED_BIDDING}; start on manual or max clicks, or merge campaigns")
    elif is_num(budget):
        add(findings, "warning", "forecast_missing", path + ".forecast", "no forecast with cpc and cvr; budget cannot be tied to a conversion target")
    # --- audience for special categories
    if plan.get("special_category") or plan.get("vertical") in SPECIAL_VERTICALS:
        aud = camp.get("audience")
        if isinstance(aud, dict):
            for key in RESTRICTED_TARGETING:
                if aud.get(key) not in (None, "", [], False):
                    add(findings, "error", "special_category_targeting", path + ".audience." + key, f"{key} targeting is not allowed for housing, credit or employment ads")
        if not plan.get("special_category"):
            add(findings, "error", "special_category_unflagged", "special_category", "vertical is housing, credit or employment: set special_category true and declare it in the platform")
    # --- negatives
    camp_negs = camp.get("negative_keywords") or []
    ad_groups = camp.get("ad_groups")
    if not isinstance(ad_groups, list) or not ad_groups:
        add(findings, "error", "no_ad_groups", path, "campaign has no ad groups")
        return
    if platform in SEARCH_PLATFORMS:
        group_negs = [n for g in ad_groups if isinstance(g, dict) for n in (g.get("negative_keywords") or [])]
        if not camp_negs and not group_negs:
            add(findings, "error", "negatives_missing", path, "search campaign has no negative keywords at campaign or ad group level")
        elif len(camp_negs) + len(group_negs) < 5:
            add(findings, "warning", "negatives_thin", path, "fewer than 5 negatives; seed with job, free, DIY, review and competitor terms")
    # --- ad groups
    campaign_utms = []
    for gi, g in enumerate(ad_groups):
        gpath = f"{path}.ad_groups[{gi}]"
        if not isinstance(g, dict):
            add(findings, "error", "ad_group_shape", gpath, "ad group must be an object")
            continue
        url = g.get("landing_url")
        if not isinstance(url, str) or not url.strip():
            add(findings, "error", "landing_url_missing", gpath, "ad group has no landing_url")
        else:
            scheme, host, _ = split_url(url)
            if scheme != "https" or not host:
                add(findings, "error", "landing_url_invalid", gpath + ".landing_url", f"'{url}' must be an absolute https URL")
            else:
                campaign_utms.append((gpath, check_utm(findings, url, gpath + ".landing_url")))
        kws = g.get("keywords") or []
        if platform in SEARCH_PLATFORMS:
            if not kws:
                add(findings, "error", "keywords_missing", gpath, "search ad group has no keywords")
            neg_all = {strip_kw(n) for n in camp_negs + (g.get("negative_keywords") or []) if isinstance(n, str)}
            for kw in kws:
                if not isinstance(kw, str):
                    continue
                k = strip_kw(kw)
                if k in neg_all:
                    add(findings, "error", "negative_blocks_keyword", gpath, f"keyword '{kw}' is also a negative; the ad group would never serve for it")
                if k in state["keywords"] and state["keywords"][k] != gpath:
                    add(findings, "warning", "keyword_overlap", gpath, f"keyword '{kw}' also in {state['keywords'][k]}; ad groups compete with each other")
                state["keywords"].setdefault(k, gpath)
        ads = g.get("ads")
        if not isinstance(ads, list) or not ads:
            add(findings, "error", "ads_missing", gpath, "ad group has no ads")
        else:
            for ai, ad in enumerate(ads):
                check_ad(plan, findings, platform, ad, f"{gpath}.ads[{ai}]")
    # --- UTM consistency inside the campaign
    for key in REQUIRED_UTM:
        vals = {u[key] for _, u in campaign_utms if key in u}
        if len(vals) > 1:
            add(findings, "error", "utm_inconsistent", path, f"{key} has {len(vals)} different values across ad groups: {sorted(vals)}")
    declared = camp.get("utm_campaign")
    if isinstance(declared, str):
        for gpath, u in campaign_utms:
            if "utm_campaign" in u and u["utm_campaign"] != declared:
                add(findings, "error", "utm_campaign_mismatch", gpath, f"utm_campaign '{u['utm_campaign']}' differs from the campaign's utm_campaign '{declared}'")
    for _, u in campaign_utms:
        if "utm_source" in u:
            state["sources"].setdefault(platform, set()).add(u["utm_source"])


def validate(plan):
    findings = []
    state = {"budget_sum": 0.0, "keywords": {}, "sources": {}}
    if not isinstance(plan.get("conversion"), dict) or not str(plan["conversion"].get("definition", "")).strip():
        add(findings, "error", "conversion_undefined", "conversion", "conversion needs a name and a written definition (what event, counted how, in what window)")
    elif not plan["conversion"].get("name"):
        add(findings, "error", "conversion_undefined", "conversion.name", "conversion has no name")
    camps = plan.get("campaigns")
    if not isinstance(camps, list) or not camps:
        add(findings, "error", "no_campaigns", "campaigns", "plan has no campaigns")
        camps = []
    for ci, camp in enumerate(camps):
        if isinstance(camp, dict):
            check_campaign(plan, findings, camp, ci, state)
        else:
            add(findings, "error", "campaign_shape", f"campaigns[{ci}]", "campaign must be an object")
    total = plan.get("total_budget")
    if is_num(total):
        if abs(total - state["budget_sum"]) > 0.01:
            add(findings, "error", "total_budget_mismatch", "total_budget", f"campaign budgets add up to {round(state['budget_sum'], 2)}, but total_budget is {total}")
    else:
        add(findings, "error", "total_budget_missing", "total_budget", "total_budget must be a number")
    for platform, sources in state["sources"].items():
        if len(sources) > 1:
            add(findings, "warning", "utm_source_varies", "campaigns", f"{platform} campaigns use several utm_source values {sorted(sources)}; reports will split one channel")
    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = len(findings) - errors
    return {
        "tool": "validate_ad_plan",
        "valid": errors == 0,
        "summary": {"errors": errors, "warnings": warnings, "campaigns": len(camps)},
        "findings": findings,
        "limits_note": "platform character limits and asset counts are verify (unconfirmed, as of 2026-11)",
    }


def emit(obj):
    if hasattr(sys.stdout, "reconfigure"):  # force UTF-8 on Windows consoles
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate an ad plan JSON file.")
    ap.add_argument("plan", help="path to the plan JSON file")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args(argv)
    try:
        with open(args.plan, "r", encoding="utf-8-sig") as fh:
            plan = json.load(fh)
    except (OSError, ValueError) as exc:
        emit({"tool": "validate_ad_plan", "valid": False, "error": f"cannot read plan: {exc}. Pass a UTF-8 JSON file."})
        return 2
    if not isinstance(plan, dict):
        emit({"tool": "validate_ad_plan", "valid": False, "error": "top level of the plan must be a JSON object"})
        return 2
    report = validate(plan)
    emit(report)
    if report["summary"]["errors"] or (args.strict and report["summary"]["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
