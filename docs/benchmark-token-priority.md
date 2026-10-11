# v2.3: token-first admission

Measured 2026-10-12, same four public real files, six exact-answer questions per file, three repeats; main model `gpt-6.1-sol` / medium. Provenance and original full-read baselines are in [the earlier report](benchmark-improvements.md). The comparison below uses v2.2 measurements from the earlier run, not simultaneous pairs. Tokens include selector + main input and output; cached input is not counted twice. Wall time includes router + main. All values below are per-file medians except accuracy.

| File | v2.2 total tokens | v2.3 total tokens | Change | v2.2 seconds | v2.3 seconds | Grounded accuracy |
|---|---:|---:|---:|---:|---:|---:|
| cpython_subprocess_timeout | 29,638 | 23,815 | -19.6% | 8.01 | 8.32 | 18/18 |
| cpython_asyncio_connections | 26,554 | 26,552 | -0.0% | 10.13 | 9.06 | 18/18 |
| cpython_ubsan_failure | 51,445 | 49,699 | -3.4% | 15.76 | 9.13 | 18/18 |
| scipy_distributed_failures | 52,569 | 51,839 | -1.4% | 13.96 | 9.35 | 18/18 |

The final run made **zero Luna calls**, scored **72/72** answers with visible original-line evidence, and required no recovery reads. Asyncio passed through whole because adding boundary context brought candidate reduction below the 15% character margin; the other files used candidate extraction. A few-token difference on whole-read cases comes from generated answer lengths, not selector usage. This policy cannot guarantee a lower final token count.

The first v2.3 experiment saved more tokens but scored **69/72**: all three asyncio trials lacked socket cleanup evidence immediately beyond a candidate boundary. The fix preserves two neighboring lines around each candidate, merges ranges, then rechecks packet size and reduction. This is a general boundary guard, not a completeness guarantee. The final run was restarted for all four files after the fix; the failed iteration was retained locally.

Default token mode has no model-based selection overhead. It admits a packet only when rendered characters are at least 15% below comparable full output and within the configured character budget; small sources pass through whole. Unhelpful large packets return exit 2 with suggested ranges and no raw text. This admission test is a character heuristic, not a tokenizer or proof of total savings. Model output length and subsequent recovery reads remain uncertain; include both when evaluating new tasks. `--force-model` and `--optimize latency` are explicit opt-ins to potential extra cloud usage.

Limitations: four regression files, three serial repeats, previously used development questions, no held-out generalization claim, uncontrolled service latency/cache state. Token savings are measured unweighted usage, not a subscription-cost calculation. The harness's legacy `router_fallback` substring flag can match source code containing “fallback”; this report reads structured router status instead. [Per-trial data and router hash](benchmark-v2.3.json).
