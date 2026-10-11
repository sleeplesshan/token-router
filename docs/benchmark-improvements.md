# Real-file benchmark: v2.1 improvements

2026-10-12. Fixed GPT-6 Luna (`low`) router, GPT-6.1 Sol (`medium`) analyzer, Codex CLI 0.162.1, existing ChatGPT login. Four unchanged public files, six factual questions per file, three repetitions per condition. Each question requires an exact answer and a visible original-line citation of at most 35 lines. This measures first-pass evidence extraction, not bug repair or complete incident diagnosis.

## Findings

v2.0 overmatched ordinary question words and spent its character budget on log prefixes. The real error evidence never reached Luna. v2.1 ranks before truncating, reserves distributed/tail evidence, filters generic question words, and preserves bounded named failure blocks. Selected model ranges receive up to two neighbor lines using only spare output budget.

| File | Lines | Full source correct | v2.0 correct | v2.1 correct |
|---|---:|---:|---:|---:|
| subprocess.py | 2,223 | 18/18 | 18/18 | 18/18 |
| asyncio/base_events.py | 2,052 | 18/18 | 18/18 | 18/18 |
| CPython UBSan CI log | 3,768 | 18/18 | 0/18 | 18/18 |
| SciPy CI log | 6,315 | 18/18 | 0/18 | 18/18 |

Tokens below include router + analyzer input/output; cached input is already part of input and is not counted twice. Time includes both CLI processes. Values are medians.

| File | Full source tokens | v2.0 tokens | v2.1 tokens | Full source seconds | v2.0 seconds | v2.1 seconds |
|---|---:|---:|---:|---:|---:|---:|
| subprocess.py | 29,634 | 35,553 | 27,836 | 8.11 | 13.41 | 12.73 |
| asyncio/base_events.py | 26,543 | 32,901 | 28,370 | 8.46 | 13.66 | 16.08 |
| CPython UBSan CI log | 224,199 | 124,385 | 50,021 | 10.54 | 13.92 | 14.15 |
| SciPy CI log | 277,788 | 67,922 | 52,567 | 10.84 | 12.60 | 17.46 |

The old log condition failed all six routing attempts, then analyzed only its emitted fallback; all 36 answers were withheld for insufficient evidence. It is not a successful token-saving result. v2.1 is a new measured run, not a regrade of the old calls.

## Retrieval policy

- Use ordinary search or `--deterministic` for known identifiers. Deterministic mode makes no model call, but its bounded output remains lossy.
- Use Luna when semantic selection is useful; read directly if candidates are nearly the whole source and full reading is practical. There is no universal file-line threshold for a beneficial cloud call.
- Check coverage/truncation and model-failure status even when extraction exits 0. Expand omitted raw evidence before concluding.
- Smaller main context does not guarantee lower total tokens, faster completion, or lower subscription usage. This benchmark does not measure subscription credits or dollar cost.

## Validation and limits

- 20 offline unit tests and 10 fixture cases pass. They cover auth isolation, malformed output, timeouts, Unicode identifiers, query overmatching, distributed evidence under a budget, repeated errors, first named traceback context, fallback, and output padding.
- 12 final routed trials (12 Luna calls + 12 analyzer calls); no parallel model calls. Full-source and v2.0 values reuse the preceding benchmark. Because conditions were measured sequentially at different times, cache state and server load were not controlled. Three repetitions are a small sample and latency is descriptive, not a causal speed claim.
- Six questions were batched in each query. This is a deliberately broad retrieval task and can be less favorable than one focused identifier. Same queries and gold answers were retained for the follow-up.
- Before the final context-padding fix, a separate development iteration scored 69/72. Those 12 routed trials are retained locally and excluded from the final-version column; the observed misses drove the generic neighbor-context correction. No gold line numbers or source-specific names were added to router logic.
- Candidate coverage and final selection remain lossy. No universal completeness guarantee follows from these four files. The skill requires source expansion for unsupported claims; this benchmark did not perform iterative expansion.
- Raw output is line-capped; the candidate character cap does not impose an output byte limit. Scanning retains metadata proportional to source line count.

## Sources and reproducibility

Per-trial counts, question/answer definitions and router hash are in [benchmark-v2.1.json](benchmark-v2.1.json). Full local CLI events and raw slices are retained with the benchmark artifacts. Timings exclude dataset preparation.

- [subprocess.py](https://github.com/python/cpython/blob/60403a5409ff2c3f3b07dd2ca91a7a3e096839c7/Lib/subprocess.py) — SHA-256 `e84782f0d4a19f6001624f21b7d5c20c610e8e27113e2fd9c0482eb1dcd760cd`
- [asyncio_base_events.py](https://github.com/python/cpython/blob/60403a5409ff2c3f3b07dd2ca91a7a3e096839c7/Lib/asyncio/base_events.py) — SHA-256 `06368fda7fba857cedfa5dec24d907b1d04f0a3ac8313e9b059b5191734ea354`
- [cpython-ubsan.log](https://github.com/python/cpython/actions/runs/38139579572/job/114470618995) — SHA-256 `d23199487e0009822f4d3a33284fb9a42da018155164c308e96cad456611d606`
- [scipy-fast.log](https://github.com/scipy/scipy/actions/runs/38118134919/job/114407140306) — SHA-256 `23cc02f4ecff02141897d670bf831f5be62702b33c2a48e6e5c2b717fd783ca3`

Final router SHA-256: `4a45f54ab44b7ae77a0a860e7d1fb30f5480e0fc19cd066ca397f8a9fe4d8e7f`.
