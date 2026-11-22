# Sources and confidence

Facts used by the skill, in my own words, with how each was established.

| Fact | Status |
|---|---|
| Q8_0 stores 32 weights in 34 bytes (a 2-byte scale and 32 one-byte values), so 8.5 bits per weight | Block-layout arithmetic; stable |
| q8_0 and q4_0 KV cache elements cost 34/32 and 18/32 bytes | Same block arithmetic, assuming the same block layout is used for the cache |
| KV cache size is 2 x layers x kv_heads x head_dim x context x bytes per element | Standard attention bookkeeping: one key and one value vector per layer per token |
| Generating one token reads every active weight once, so bandwidth divided by model bytes is a ceiling | Standard memory-bound argument; real speed is lower |
| Bits per weight for Q6_K, Q5_K_M, Q4_K_M, Q3_K_M, Q2_K (6.56, 5.69, 4.85, 3.91, 2.63) | Commonly quoted averages; verify (unconfirmed, as of 2026-11) |
| Quality-loss notes per quant | Community consensus, not measured here; verify (unconfirmed, as of 2026-11) |
| OS reserve (4, 4, 2 GB), GPU reserve 0.5 GB, activation 0.5 GB, headroom 10 percent, 8B-class KV fallback | House working assumptions; overridable where marked in the spec |
| Share of Apple unified memory the GPU may use | Not stated by the skill; verify (unconfirmed, as of 2026-11) |

Where to check: the llama.cpp project page (https://github.com/ggml-org/llama.cpp) for quantization types and the runtime's load log, which prints the real buffer sizes. Model cards give layers, KV heads, head dimension and trained context.
