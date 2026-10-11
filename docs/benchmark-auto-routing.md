# Automatic model-call bypass — v2.2.0

Measured 2026-10-12 with the same four public files, six factual questions each and three repetitions. Router remains GPT-6 Luna low; analyzer remains GPT-6.1 Sol medium through Codex CLI 0.162.1 and the existing ChatGPT login. Prior v2.1 measurements are reused for comparison.

Default routing now returns a whole small source (up to 12,000 raw characters), or a moderate source up to 100,000 characters when selected candidate raw text covers at least 65%. This full-source path deliberately preserves every line beyond the usual 160-line selection limit. Small untruncated candidates may bypass Luna when they fit both 12,000 characters and the output line cap, with all normalized query terms in source text. Other cases still use Luna. Thresholds are initial heuristics, not token limits or universal break-even points.

| File | Luna calls v2.1 → v2.2 | Seconds v2.1 → v2.2 | Combined tokens v2.1 → v2.2 | Grounded correct v2.1 → v2.2 |
|---|---:|---:|---:|---:|
| subprocess.py | 3 → 0 | 12.73 → 8.01 | 27,836 → 29,638 | 18/18 → 18/18 |
| asyncio/base_events.py | 3 → 0 | 16.08 → 10.13 | 28,370 → 26,554 | 18/18 → 18/18 |
| CPython UBSan log | 3 → 3 | 14.15 → 15.76 | 50,021 → 51,445 | 18/18 → 18/18 |
| SciPy log | 3 → 3 | 17.46 → 13.96 | 52,567 → 52,569 | 18/18 → 18/18 |

Tokens and time are medians, including router plus analyzer. Cached tokens remain part of input and are not double-counted. Code trials eliminated all six Luna calls and were about 37% faster than the previous routed measurements. The two large logs continued to use Luna; their timing differences are not attributed to this bypass change. All 72 factual answers retained valid source evidence.

Bypassing selection can increase main input: subprocess combined tokens rose about 6.5%. Speed and token savings are separate outcomes. This does not establish subscription-credit or dollar savings. The previous direct-source benchmark is in [the v2.1 report](benchmark-improvements.md).

## Checks and limits

- 28 offline unit tests and 10 fixture regressions pass. Coverage includes threshold boundaries, raw-character density, uncapped full-source preservation, query matching without injected line labels, sparse large-source candidate bypass, and explicit overrides.
- `--force-model` disables automatic bypass. `--deterministic` explicitly requires bounded Python-only extraction. They are mutually exclusive.
- `model_called=false` and zero routing usage distinguish skipped model calls. `auto_candidates` can still omit relevant source; `coverage_guaranteed=true` for `auto_full` refers only to returning the whole source, not answer correctness.
- The 12 measured trials used six Luna calls plus 12 analyzer calls. Model calls ran serially. Cache state and server load were not controlled, and the comparison uses earlier v2.1 runs rather than randomized contemporaneous pairs. Three repetitions are descriptive, not a general latency guarantee.
- After measurement, a numeric/gap-label query-match guard was added. Offline replay confirmed all 12 measured route decisions unchanged, with the cloud prompt and call path unchanged. No additional model measurement is claimed for that guard.
- No cache or automatic retry was introduced.

Sources, exact questions and gold criteria remain those in [benchmark-v2.1.json](benchmark-v2.1.json). Summary and per-trial counts are in [benchmark-v2.2.json](benchmark-v2.2.json). Raw CLI events are retained in local benchmark artifacts.

Measured router SHA-256: `1bf0c079dc62499401e07b904e1378c12070ef2b360a2d3d5ba656bd20a17e0f`.

Released router SHA-256: `de04848ca716c2fc9c1714ebf8b679a69e2e2eb416292af8cd7d638ac5260d46`.
