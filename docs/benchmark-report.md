# Token Router Benchmark Report

## v2 status

Version 2.0.0 uses Codex CLI with fixed `gpt-6-luna` and `low` reasoning effort. The measurements below were collected for **v1 on 2026-06-02 using a local model**. They are retained as historical provenance, not current performance claims. No comparative GPT-6 Luna benchmark is reported here.

Main-agent context reduction excludes the input processed by the routing model. Real v2 calls send candidate content to the cloud and consume Codex subscription usage. Output shrinkage alone therefore cannot establish total token savings, monetary savings, latency improvements, or correctness.

## v2 live smoke checks — 2026-10-11 (KST)

These checks used `codex-cli 0.162.1`, ChatGPT authentication, and fixed `gpt-6-luna` with `low` reasoning. Each tiny synthetic fixture was run once with `--real`. All four passed without deterministic fallback. Usage below is reported by the CLI; cached input and reasoning tokens were both zero in every case.

| Fixture | Elapsed | Input tokens | Output tokens | Result |
|---|---:|---:|---:|---|
| Source token expiration | 3.79s | 5,040 | 37 | Pass; no fallback |
| Streaming late log error | 3.32s | 5,614 | 39 | Pass; no fallback |
| Agent-context deployment | 4.08s | 5,183 | 49 | Pass; no fallback |
| Agent-context frontend | 4.33s | 5,187 | 39 | Pass; no fallback |

This verifies live integration and fixture expectations, not comparative speed, quality, cost, or production reliability. The roughly 5,000 input tokens even for tiny fixtures indicate substantial CLI/framework overhead in addition to candidate text. Avoid routing short inputs where that overhead is unlikely to be worthwhile. These checks do not isolate the exact overhead or measure repeated-run variability, downstream task success, or main-agent savings.

## Historical v1 environment and results

The old backend used Ollama with `gemma4:e2b-it-q4_K_M`, a 4096-token context setting, immediate unloading, and a 60-second timeout. That backend is removed in v2; these are not current setup instructions. Token counts were estimated using `chars / 4`, not a billing tokenizer.

| Case | Mode | Lines | Full file estimated tokens | Output estimated tokens | Reduction | Time | Fallback |
|---|---|---:|---:|---:|---:|---:|---|
| Sparse infra log | `error_log` | 2,000 | 41,711 | 131 | 99.69% | 5.37s | No |
| Legacy bug source | `heavy_code` | 2,155 | 7,520 | 70 | 99.06% | 4.46s | No |
| Keywordless structural source | `heavy_code` | 504 | 4,188 | 48 | 98.85% | 6.13s | No |

The original report described ten mock regression cases for query pass-through, range merging, caps, streaming tails, and optional instruction-reference selection. It also recorded successful model smoke checks and confirmed the local model unloaded afterward. These observations do not validate the v2 cloud integration or Luna's selection quality.

## Evaluating v2

Use identical fixtures, queries, prefilter limits, and output caps for each comparison. Include a deterministic prefilter-only baseline and, if historical code is intentionally restored for comparison, label that separate v1 environment explicitly.

Record:

- Relevant-line recall and omitted dependencies against annotated evidence.
- Final task success when the main reasoning model receives the selected evidence.
- End-to-end elapsed time, including CLI startup, request latency, retries, and fallback.
- Routing input/output and main-agent input separately, using actual usage data when available.
- CLI version, fixed model/effort, account/model availability, repeated-run variability, and failures.

Run the mock suite for mechanics; `--real` exercises the actual service and consumes usage. Mock success does not measure model quality. A selected slice preserves original text but can omit essential context. Root instructions already injected into an agent's session cannot be made cheaper retroactively by routing.
