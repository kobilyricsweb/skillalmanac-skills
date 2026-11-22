---
name: local-model-sizing
description: Works out whether an open-weight language model will run on a given GPU, Mac or PC, with a script that computes weight, KV-cache and overhead memory per quantization (FP16 down to Q2_K), a fit verdict per machine, the largest context that fits, and a tokens-per-second ceiling from memory bandwidth. Use when the user asks will this model run on my GPU, how much VRAM or RAM do I need, which quant to pick for Ollama, llama.cpp or LM Studio, or why a local LLM is slow or out of memory. Do not use for cloud API pricing, training or fine-tuning memory, picking a model by quality, or installing runtimes.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, use the formulas in the body by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Local model sizing

Answer "will it run, and how well" with a memory budget the user can check, not a guess. Every figure comes from a formula below or is marked "verify (unconfirmed, as of 2026-11)". Never quote a benchmark or a tokens-per-second figure as a measurement; speed here is a ceiling.

## Workflow

```
- [ ] 1 Collect inputs
- [ ] 2 Write spec.json
- [ ] 3 Run scripts/size_model.py
- [ ] 4 Read warnings first
- [ ] 5 Pick the quant from the verdict table
- [ ] 6 Report in the fixed shape
```

1. **Collect inputs.** Ask only for what is missing: model name and parameter count (billions); for each machine, VRAM, system RAM, OS, whether memory is unified (Apple silicon), GPU count; target context in tokens; use (chat, coding, long_documents). Wanted when known: layers, KV heads, head dim, trained context (from the model card or its GGUF metadata), memory bandwidth of the GPU and of system RAM. For a mixture-of-experts model (MoE) get total and active parameters; they are different numbers and must not be swapped. Never invent a model's architecture: if the user does not know it, leave the fields out and the script labels the KV estimate approximate.
2. **Write the spec.** Field names and types are in [references/spec_format.md](references/spec_format.md); read it when writing the file or when the script rejects one.
3. **Run it.** `python scripts/size_model.py spec.json`. Prints one JSON document; exit 0 when something fits, 1 when nothing fits, 2 for a bad spec (message on stderr). Run it; do not edit it. Without Python, use the manual formulas below and say the result is hand-computed.
4. **Read `warnings` first** (top level, per machine, per row). Each one changes how far a number can be trusted.
5. **Pick the quant** with the tables below, then give the three-line recommendation per machine that the script already prints, adjusted by your judgement of the use.
6. **Report** in the shape at the end.

## Formulas (decimal GB, all assumptions stated)

- Weights GB = parameters in billions x bits per weight / 8.
- KV cache bytes = 2 x layers x kv_heads x head_dim x context x bytes per element. Bytes per element: f16 2; q8_0 34/32 = 1.0625; q4_0 18/32 = 0.5625 (block layout arithmetic).
- Total = weights + KV + 0.5 GB activation/scratch (assumption; larger at big batch sizes).
- Needed = Total x 1.10 (the 10 percent headroom rule). A model "fits" only if Needed is at most the pool.
- Pool, discrete GPU: VRAM minus 0.5 GB per GPU (display and driver, assumption). System RAM pool: RAM minus OS reserve (Windows 4, macOS 4, Linux 2 GB; assumptions, overridable in the spec). Unified memory: RAM minus OS reserve is the only pool.
- Speed ceiling tokens/s = bandwidth in GB/s / GB read per token. Dense model: all weights. MoE: active parameters only. Partial offload: 1 / (GPU share x bytes / GPU bandwidth + CPU share x bytes / RAM bandwidth). The real speed is lower; say so every time.

## Quantization ladder

| Quant | Bits per weight | Note |
|---|---|---|
| FP16 | 16.0 (exact) | Reference; rarely worth its memory for inference |
| Q8_0 | 8.5 (exact: 34 bytes per 32 weights) | Difference from FP16 usually hard to notice (verify (unconfirmed, as of 2026-11)) |
| Q6_K | about 6.56 | Close to Q8_0 (verify (unconfirmed, as of 2026-11)) |
| Q5_K_M | about 5.69 | Quality-first choice (verify (unconfirmed, as of 2026-11)) |
| Q4_K_M | about 4.85 | Common default (verify (unconfirmed, as of 2026-11)) |
| Q3_K_M | about 3.91 | Visible loss on code and reasoning reported (verify (unconfirmed, as of 2026-11)) |
| Q2_K | about 2.63 | Last resort; heavy loss (verify (unconfirmed, as of 2026-11)) |

Choice rule: take the highest-bit quant whose verdict is `fits_fully` at the user's context. If the best fully fitting quant is Q3_K_M or below and Q4_K_M fits with partial offload, show both and let the user trade speed against quality. A smaller model at Q5 or Q6 often beats a larger one at Q2 or Q3; say so when the only fit is Q2_K.

## Verdicts

| Verdict | Condition | Advice |
|---|---|---|
| fits_fully | Needed at most the fast pool (VRAM or unified) | Best case; speed bound by that memory's bandwidth |
| partial_offload | Needed above VRAM but at most VRAM plus RAM pool, and at least 10 percent of the model fits on the GPU | Works; the script reports the approximate GPU share and layers; speed drops toward RAM speed |
| cpu_only | No usable GPU, or under 10 percent would fit on it, and Needed at most the RAM pool | Works for small models; speed bound by RAM bandwidth |
| does_not_fit | Otherwise | Lower context, smaller model, smaller quant, or more memory; read `max_context_with_offload` |

Speed class from the ceiling (working values, not measured): 25 tokens/s or more fast; 8 to 25 comfortable; 2 to 8 usable for chat; under 2 slow, below reading speed. Long prompts add prompt-processing time that this ceiling ignores.

## Traps the script checks

- Zero or negative inputs stop the run (exit 2).
- Context above the model's trained limit: warning, and `max_context` is capped at the limit.
- KV cache dtype other than f16: warning; runtimes need an option to enable it and the quality cost is not measured here.
- MoE: memory uses total parameters, speed uses active parameters. Without `active_params_b` no speed ceiling is given.
- Several GPUs count only when the user says layers can be split (`split_layers: true`); otherwise one GPU is used and a warning says so.
- macOS unified memory: the GPU may be allowed less than the pool shown (verify (unconfirmed, as of 2026-11)).
- Missing layers, kv_heads or head_dim: the KV figure is approximate (8B-class shape scaled by parameters); say so in the report.

## Report shape

```
Machine: <name> | Model: <name> | Context: <tokens> | KV dtype: <dtype>
Verdict: <best quant> -> <verdict>, needs <GB> with headroom, pool <GB>
Speed ceiling: <tokens/s> (class), real speed lower; bandwidth used: <which>
Largest context at that quant: <tokens>
Approximate: <KV estimate? unconfirmed bits per weight? bandwidth guessed?>
Not checked: <runtime overhead, real load, actual speed, model quality at this quant>
```

## Limits

- Estimates, not measurements: runtime overhead, flash attention, batch size, memory fragmentation and the exact quant mix of a given file all move the real number. Confirm with the runtime's own load log.
- Bits per weight for K-quants and the quality notes are unconfirmed averages; a real file's size on disk is the better figure when the user has it, and the weights term can be replaced by it.
- Speed is a bandwidth ceiling only; compute-bound cases (prompt processing, tiny GPUs) can be slower. No benchmark is stated or implied.
- Not covered: training or fine-tuning memory, speculative decoding, tensor-parallel multi-node setups, vision or audio encoders, diffusion models.
- Hardware prices, availability and model rankings are outside scope.
- Which facts are exact arithmetic and which are unconfirmed is listed in [references/sources.md](references/sources.md); read it when the user challenges a number.
