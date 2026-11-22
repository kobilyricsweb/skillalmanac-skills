#!/usr/bin/env python3
"""Compute whether a language model fits in memory, per quantization and per machine.

Usage:
    python scripts/size_model.py spec.json

Reads one JSON spec file (see references/spec_format.md). Writes nothing and uses
no network. Prints one JSON document to stdout.

Exit codes:
    0  valid spec, at least one machine can hold at least one quantization
    1  valid spec, but no machine can hold any quantization
    2  unreadable or invalid spec (plain message on stderr)

All sizes are decimal gigabytes (1 GB = 1,000,000,000 bytes). Every constant below
is an assumption, labelled as such in the output. Speed figures are ceilings.
"""
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Bits per weight, including block scales. Q8_0 is exact arithmetic: 34 bytes
# hold 32 weights = 8.5 bits. The K-quant figures are commonly quoted averages
# and are not confirmed here, so the output marks them "verify".
QUANTS = [
    ("FP16", 16.0, "exact"),
    ("Q8_0", 8.5, "exact"),
    ("Q6_K", 6.56, "verify (unconfirmed, as of 2026-11)"),
    ("Q5_K_M", 5.69, "verify (unconfirmed, as of 2026-11)"),
    ("Q4_K_M", 4.85, "verify (unconfirmed, as of 2026-11)"),
    ("Q3_K_M", 3.91, "verify (unconfirmed, as of 2026-11)"),
    ("Q2_K", 2.63, "verify (unconfirmed, as of 2026-11)"),
]

# Bytes per KV-cache element. f16 is 2. q8_0 is 34 bytes per 32 values and q4_0 is
# 18 bytes per 32 values (block format arithmetic).
KV_BYTES = {"f16": 2.0, "q8_0": 34.0 / 32.0, "q4_0": 18.0 / 32.0}

HEADROOM = 1.10  # house rule: keep 10 percent of the pool free after the estimate
ACTIVATION_GB = 0.5  # assumption: compute and scratch buffers at modest batch size
GPU_RESERVE_GB = 0.5  # assumption: display and driver use on a desktop discrete GPU
OS_RESERVE_GB = {"windows": 4.0, "macos": 4.0, "linux": 2.0}  # assumptions
MIN_GPU_SHARE = 0.10  # below this share of the model on the GPU, treat the run as CPU only
# Fallback KV size when layers, kv_heads or head_dim are missing: bytes per token
# per billion parameters at f16, from one 8B-class shape (2 x 32 x 8 x 128 x 2 bytes
# = 131,072 per token over 8 billion parameters). Approximate by construction.
KV_FALLBACK_BYTES_PER_B = 16384.0
MIN_CONTEXT_BY_USE = {"chat": 8192, "coding": 16384, "long_documents": 32768}  # working values
# Speed classes from the tokens-per-second ceiling (working values, not measured).
SPEED_CLASSES = [(25.0, "fast"), (8.0, "comfortable"), (2.0, "usable for chat"), (0.0, "slow, below reading speed")]

QUALITY_NOTES = {
    "FP16": "reference quality; usually more memory than needed",
    "Q8_0": "difference from FP16 is typically hard to notice; verify (unconfirmed, as of 2026-11)",
    "Q6_K": "very close to Q8_0 in most reports; verify (unconfirmed, as of 2026-11)",
    "Q5_K_M": "small loss, a common quality-first choice; verify (unconfirmed, as of 2026-11)",
    "Q4_K_M": "common default; modest loss; verify (unconfirmed, as of 2026-11)",
    "Q3_K_M": "visible loss on reasoning and code is commonly reported; verify (unconfirmed, as of 2026-11)",
    "Q2_K": "heavy loss; last resort for very large models; verify (unconfirmed, as of 2026-11)",
}


class SpecError(Exception):
    pass


def num(obj, key, where, required=True, positive=True):
    if key not in obj or obj[key] is None:
        if required:
            raise SpecError(f"{where}.{key} is required")
        return None
    v = obj[key]
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SpecError(f"{where}.{key} must be a number, got {v!r}")
    if positive and v <= 0:
        raise SpecError(f"{where}.{key} must be greater than zero, got {v}")
    if not positive and v < 0:
        raise SpecError(f"{where}.{key} must not be negative, got {v}")
    return float(v)


def kv_per_token_bytes(model, kv_dtype):
    """Return (bytes per token, approximate flag)."""
    layers, kvh, hd = model.get("layers"), model.get("kv_heads"), model.get("head_dim")
    if layers and kvh and hd:
        return 2.0 * layers * kvh * hd * KV_BYTES[kv_dtype], False
    scale = KV_BYTES[kv_dtype] / 2.0
    return KV_FALLBACK_BYTES_PER_B * model["params_b"] * scale, True


def speed_class(tps):
    for floor, label in SPEED_CLASSES:
        if tps >= floor:
            return label
    return SPEED_CLASSES[-1][1]


def validate(spec):
    if not isinstance(spec, dict):
        raise SpecError("spec must be a JSON object")
    m = spec.get("model")
    if not isinstance(m, dict):
        raise SpecError("model object is required")
    model = {"name": str(m.get("name", "unnamed model")), "moe": bool(m.get("moe", False))}
    model["params_b"] = num(m, "params_b", "model")
    model["active_params_b"] = num(m, "active_params_b", "model", required=False)
    for k in ("layers", "kv_heads", "head_dim"):
        v = num(m, k, "model", required=False)
        model[k] = int(v) if v else None
    model["trained_context"] = num(m, "trained_context", "model", required=False)
    if model["moe"] and model["active_params_b"] and model["active_params_b"] >= model["params_b"]:
        raise SpecError("model.active_params_b must be smaller than model.params_b for a MoE model")
    context = num(spec, "context", "spec")
    kv_dtype = str(spec.get("kv_dtype", "f16")).lower()
    if kv_dtype not in KV_BYTES:
        raise SpecError(f"spec.kv_dtype must be one of {sorted(KV_BYTES)}, got {kv_dtype!r}")
    use = str(spec.get("use", "chat")).lower()
    if use not in MIN_CONTEXT_BY_USE:
        raise SpecError(f"spec.use must be one of {sorted(MIN_CONTEXT_BY_USE)}, got {use!r}")
    hw = spec.get("hardware")
    if not isinstance(hw, list) or not hw:
        raise SpecError("hardware must be a non-empty list")
    machines = []
    for i, h in enumerate(hw):
        where = f"hardware[{i}]"
        if not isinstance(h, dict):
            raise SpecError(f"{where} must be an object")
        os_name = str(h.get("os", "linux")).lower()
        if os_name not in OS_RESERVE_GB:
            raise SpecError(f"{where}.os must be one of {sorted(OS_RESERVE_GB)}, got {os_name!r}")
        mach = {
            "name": str(h.get("name", f"machine {i + 1}")),
            "os": os_name,
            "unified": bool(h.get("unified", False)),
            "split_layers": bool(h.get("split_layers", False)),
            "vram_gb": num(h, "vram_gb", where, required=False, positive=False) or 0.0,
            "ram_gb": num(h, "ram_gb", where),
            "gpu_bandwidth_gbps": num(h, "gpu_bandwidth_gbps", where, required=False),
            "ram_bandwidth_gbps": num(h, "ram_bandwidth_gbps", where, required=False),
            "os_reserve_gb": num(h, "os_reserve_gb", where, required=False, positive=False),
        }
        g = num(h, "gpus", where, required=False)
        mach["gpus"] = int(g) if g else 1
        if mach["os_reserve_gb"] is None:
            mach["os_reserve_gb"] = OS_RESERVE_GB[os_name]
        if not mach["unified"] and mach["vram_gb"] == 0.0:
            mach["gpus"] = 0
        machines.append(mach)
    return model, context, kv_dtype, use, machines


def pools(mach, warnings):
    """Return (fast_pool_gb, slow_pool_gb). fast is VRAM or the unified pool."""
    cpu_pool = max(mach["ram_gb"] - mach["os_reserve_gb"], 0.0)
    if mach["unified"]:
        if mach["os"] == "macos":
            warnings.append("unified memory on macOS: the share the GPU may use can be below the pool shown; verify (unconfirmed, as of 2026-11)")
        return cpu_pool, 0.0
    usable_gpus = mach["gpus"]
    if mach["gpus"] > 1 and not mach["split_layers"]:
        usable_gpus = 1
        warnings.append("several GPUs listed but split_layers is false: only one GPU is counted")
    gpu_pool = max(mach["vram_gb"] * usable_gpus - GPU_RESERVE_GB * usable_gpus, 0.0) if usable_gpus else 0.0
    return gpu_pool, cpu_pool


def max_ctx(pool_gb, weights_gb, per_tok, trained):
    avail = pool_gb / HEADROOM - weights_gb - ACTIVATION_GB
    if avail <= 0:
        return 0
    ctx = int(avail * 1e9 // per_tok)
    if trained:
        ctx = min(ctx, int(trained))
    return ctx


def evaluate_quant(qname, bpw, bpw_note, model, context, per_tok, kv_approx, mach, fast, slow):
    weights_gb = model["params_b"] * bpw / 8.0
    kv_gb = per_tok * context / 1e9
    total = weights_gb + kv_gb + ACTIVATION_GB
    need = total * HEADROOM
    warns = []
    entry = {
        "quant": qname,
        "bits_per_weight": bpw,
        "bits_per_weight_status": bpw_note,
        "quality_note": QUALITY_NOTES[qname],
        "weights_gb": round(weights_gb, 2),
        "kv_gb": round(kv_gb, 2),
        "activation_gb": ACTIVATION_GB,
        "total_gb": round(total, 2),
        "needed_with_headroom_gb": round(need, 2),
    }
    if kv_approx:
        warns.append("KV estimate is approximate: layers, kv_heads or head_dim missing")
    # What each token must read: active weights for MoE, all weights for dense.
    if model["moe"]:
        read_gb = model["active_params_b"] * bpw / 8.0 if model["active_params_b"] else None
    else:
        read_gb = weights_gb
    gpu_bw, ram_bw = mach["gpu_bandwidth_gbps"], mach["ram_bandwidth_gbps"]
    verdict, gpu_share, tps = None, None, None
    if mach["unified"]:
        bw = gpu_bw or ram_bw
        if need <= fast:
            verdict = "fits_fully"
            tps = (bw / read_gb) if (bw and read_gb) else None
        else:
            verdict = "does_not_fit"
    else:
        if fast > 0 and need <= fast:
            verdict = "fits_fully"
            tps = (gpu_bw / read_gb) if (gpu_bw and read_gb) else None
        elif fast > 0 and need <= fast + slow and fast / need >= MIN_GPU_SHARE:
            verdict = "partial_offload"
            gpu_share = fast / need
            if read_gb and gpu_bw and ram_bw:
                secs = read_gb * gpu_share / gpu_bw + read_gb * (1 - gpu_share) / ram_bw
                tps = 1.0 / secs
            if model["layers"]:
                entry["approx_gpu_layers"] = int(model["layers"] * gpu_share)
            entry["approx_gpu_share"] = round(gpu_share, 2)
        elif need <= slow:
            verdict = "cpu_only"
            tps = (ram_bw / read_gb) if (ram_bw and read_gb) else None
        else:
            verdict = "does_not_fit"
    entry["verdict"] = verdict
    if verdict != "does_not_fit":
        if tps is None:
            entry["tokens_per_second_ceiling"] = None
            warns.append("no speed ceiling: bandwidth for the memory in use (or active_params_b for MoE) not supplied")
        else:
            entry["tokens_per_second_ceiling"] = round(tps, 1)
            entry["speed_class"] = speed_class(tps)
    else:
        entry["tokens_per_second_ceiling"] = None
    # Primary pool: VRAM or the unified pool; plain system RAM when there is no GPU.
    primary = fast if fast > 0 else slow
    entry["max_context"] = max_ctx(primary, weights_gb, per_tok, model["trained_context"])
    entry["max_context_with_offload"] = max_ctx(fast + slow, weights_gb, per_tok, model["trained_context"])
    entry["warnings"] = warns
    return entry


def recommend(model, context, entries, mach):
    rank = {"fits_fully": 0, "partial_offload": 1, "cpu_only": 2}
    usable = [e for e in entries if e["verdict"] in rank]
    if not usable:
        return [
            f"{mach['name']}: no quantization of {model['name']} fits at context {int(context)}.",
            "Lower the context, pick a smaller model, or add memory; see max_context_with_offload per row.",
            "All figures are estimates with 10 percent headroom; verify with the runtime's own load log.",
        ]
    best_rank = min(rank[e["verdict"]] for e in usable)
    best = max((e for e in usable if rank[e["verdict"]] == best_rank), key=lambda e: e["bits_per_weight"])
    tps = best.get("tokens_per_second_ceiling")
    speed = f"speed ceiling about {tps} tokens/s, class '{best.get('speed_class')}'; real speed is lower" if tps else "no speed ceiling (bandwidth or active parameters not supplied)"
    return [
        f"{mach['name']}: best fit is {best['quant']} ({best['verdict']}), needs {best['needed_with_headroom_gb']} GB with headroom at context {int(context)}.",
        speed + ".",
        f"Largest context for {best['quant']} in the memory it runs from: {best['max_context']} tokens.",
    ]


def build(spec):
    model, context, kv_dtype, use, machines = validate(spec)
    global_warns = []
    if model["trained_context"] and context > model["trained_context"]:
        global_warns.append(f"context {int(context)} is above the trained limit {int(model['trained_context'])}; quality past the limit is not guaranteed")
    if context < MIN_CONTEXT_BY_USE[use]:
        global_warns.append(f"context {int(context)} is below the working minimum {MIN_CONTEXT_BY_USE[use]} for use '{use}'")
    if kv_dtype != "f16":
        global_warns.append(f"KV cache dtype {kv_dtype}: runtimes usually need a specific option to enable it, and quality cost is unmeasured here; verify (unconfirmed, as of 2026-11)")
    if "kv_bytes_per_element" in spec and abs(float(spec["kv_bytes_per_element"]) - KV_BYTES[kv_dtype]) > 0.01:
        global_warns.append(f"kv_bytes_per_element {spec['kv_bytes_per_element']} does not match dtype {kv_dtype} ({round(KV_BYTES[kv_dtype], 4)}); the dtype value was used")
    if model["moe"]:
        global_warns.append("MoE model: memory uses TOTAL parameters, speed uses ACTIVE parameters; do not mix them")
        if not model["active_params_b"]:
            global_warns.append("MoE model without active_params_b: no speed ceiling can be computed")
    elif model["active_params_b"]:
        global_warns.append("active_params_b ignored because moe is false")
    per_tok, kv_approx = kv_per_token_bytes(model, kv_dtype)
    out_hw = []
    any_fit = False
    for mach in machines:
        hw_warns = []
        fast, slow = pools(mach, hw_warns)
        entries = [evaluate_quant(q, b, n, model, context, per_tok, kv_approx, mach, fast, slow) for q, b, n in QUANTS]
        any_fit = any_fit or any(e["verdict"] != "does_not_fit" for e in entries)
        out_hw.append({
            "name": mach["name"],
            "fast_pool_gb": round(fast, 2),
            "slow_pool_gb": round(slow, 2),
            "os_reserve_gb": mach["os_reserve_gb"],
            "warnings": hw_warns,
            "per_quant": entries,
            "recommendation": recommend(model, context, entries, mach),
        })
    result = {
        "inputs": {
            "model": model, "context": int(context), "kv_dtype": kv_dtype, "use": use,
            "kv_bytes_per_token": int(per_tok), "kv_estimate_approximate": kv_approx,
            "assumptions": {
                "headroom_factor": HEADROOM, "activation_gb": ACTIVATION_GB,
                "gpu_reserve_gb_per_gpu": GPU_RESERVE_GB, "gb_is": "decimal (1e9 bytes)",
                "kv_formula": "2 x layers x kv_heads x head_dim x context x bytes_per_element",
                "speed_formula": "bandwidth_gbps / gigabytes_read_per_token (ceiling)",
            },
        },
        "warnings": global_warns,
        "hardware": out_hw,
    }
    return result, any_fit


def main(argv):
    if len(argv) != 1:
        print("usage: size_model.py spec.json", file=sys.stderr)
        return 2
    try:
        with open(argv[0], encoding="utf-8") as fh:
            spec = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"cannot read spec {argv[0]!r}: {exc}", file=sys.stderr)
        return 2
    try:
        result, any_fit = build(spec)
    except SpecError as exc:
        print(f"invalid spec: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if any_fit else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
