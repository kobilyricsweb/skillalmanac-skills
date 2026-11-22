# Listing: local-model-sizing

## One-line summary

Computes whether a local LLM fits a given GPU, Mac or PC, per quantization, with assumptions shown.

## What it does

The agent collects the machine (VRAM, RAM, bandwidth, OS), the model (parameters, and layers, KV heads and head dimension when known) and the target context. It writes a small JSON spec and runs `scripts/size_model.py`, which computes weight memory, KV-cache memory (2 x layers x kv_heads x head_dim x context x bytes per element), an activation allowance and a 10 percent headroom, then gives a verdict per quantization from FP16 to Q2_K: fits fully, partial offload, CPU only, or does not fit. It also gives the largest context that fits and a tokens-per-second ceiling from memory bandwidth. Warnings cover context past the trained limit, a quantized KV cache, mixture-of-experts models, several GPUs without a confirmed split, and a missing architecture.

## Capabilities

- Per-quantization memory table with a verdict for each machine
- Largest context per quantization, capped at the trained limit
- Speed ceiling (never a benchmark), using active parameters for MoE models
- Three-line recommendation per machine and a fixed report shape
- Every constant stated; unconfirmed numbers marked "verify (unconfirmed, as of 2026-11)"

## When to use / when not to

Use: "will this model run on my GPU", "how much VRAM for 32k context", "which quant for Ollama or llama.cpp", "why is my local model out of memory or slow".
Not for: cloud API cost (a different job), fine-tuning memory, choosing a model by quality, installing runtimes, hardware shopping advice.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the formulas in `SKILL.md` can be applied by hand.

## Install

Copy the `local-model-sizing` folder (without `LISTING.md`, `VERIFICATION.md`, `evals/`) into `.claude/skills/` or `.agents/skills/`. Install commands pinned to a release are added at publication.

## Examples

Prompt: "Will an 8B dense model (32 layers, 8 KV heads, head dim 128) run on my laptop with 8 GB VRAM and 16 GB RAM at 8192 context?" (fixture `evals/fixtures/dense_8b.json`, second machine)

Real output (excerpt of the script's JSON, `Q4_K_M` row and recommendation):

```
weights_gb 4.85, kv_gb 1.07, total_gb 6.42, needed_with_headroom_gb 7.07
verdict fits_fully, tokens_per_second_ceiling 61.9, max_context 11201
"8 GB laptop GPU: best fit is Q4_K_M (fits_fully), needs 7.07 GB with headroom at context 8192."
```

In the same run `Q5_K_M` is `partial_offload` (about 94 percent on the GPU) and `FP16` is `partial_offload` (about 39 percent on the GPU, ceiling 4.6 tokens/s).

Prompt: a 30B mixture-of-experts model with 3B active parameters on a 64 GB unified-memory Mac at 32768 context (`evals/fixtures/moe_30b.json`). Real result: FP16 does not fit (70.09 GB needed against a 60 GB pool); Q4_K_M needs 24.1 GB and has a ceiling of 219.9 tokens/s computed from the 3B active parameters; a warning says the GPU's share of unified memory is unverified.

## Limits

Estimates, not measurements. Runtime overhead, flash attention, batch size and a real file's exact quant mix change the real figure. Speed is a bandwidth ceiling. K-quant bits per weight and quality notes are unconfirmed averages. Training and fine-tuning memory are not covered.

## Evidence

Static lint and 6 script fixture cases only; see `VERIFICATION.md`. No with-skill versus baseline eval, no trigger test, no cross-tool run, no human review.

## Demo script (60 to 90 seconds)

1. Prompt: "Will a 8B model run on my 8 GB laptop? What quant?"
2. The agent asks for the missing numbers (RAM, context, bandwidth) and writes `spec.json`.
3. It runs `size_model.py`; the table shows Q4_K_M fits with 7.07 GB needed, Q5_K_M and above need partial offload.
4. The agent reads the warnings, then reports the verdict, the largest context (11,201 tokens) and the speed as a ceiling, with a "not checked" line.
Before: "should be fine with 4-bit". After: a budget with every assumption visible.

## FAQ seeds

- Does it need network access? No.
- Does it download models or run benchmarks? No; it only does arithmetic on numbers you supply.
- Why is the speed a ceiling? Generation is limited by how fast weights stream from memory, and real runs are slower.
- How is it different from a cost estimator for APIs? This one budgets your own memory; it does not price tokens.
- Why are some numbers marked "verify"? Bits per weight for K-quants and quality notes are unconfirmed averages.
- Does it handle MoE models? Yes: memory from total parameters, speed from active parameters.
- Does it cover fine-tuning? No.

## Overlap check

No existing skill in batches 01 to 05 sizes local-model memory. Nearest by topic: `library-docs-lookup` (documentation, not hardware) and `infrastructure-as-code-review` (cloud config); neither computes memory budgets.

## Changelog

0.1.0, 2026-11-21: first draft; lint and script fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5 with AI assistance; the accountable editor is Global Media Holdings. No human review has yet taken place.
