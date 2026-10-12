# Project Memory

## Hot Memory

- [decision][refs:4][last_referenced:2026-10-13][last_verified:2026-10-13] Default token optimization makes no selector-model call. Candidate admission uses rendered characters, not guaranteed total-token savings; whole read or targeted search is preferable when reduction is insufficient. Evidence: scripts/router.py, tests/test_token_priority.py, docs/benchmark-token-priority.md.
- [constraint][refs:2][last_referenced:2026-10-12][last_verified:2026-10-12] Preserve candidate boundary context before admission. Initial direct candidates lost cleanup evidence despite overlapping gold ranges; final regression measurements are72/72 with two-line neighbors and whole-read fallback. Evidence: docs/benchmark-v2.3.json. This is not a general completeness guarantee.

- [decision][refs:1][last_referenced:2026-10-12][last_verified:2026-10-12] Separate observable lexical anchors, syntax-boundary status, and packet admission. No matched query term in candidate cores triggers full reading or targeted search; this is not semantic absence or calibrated confidence. Python statement completion is bounded and can raise total tokens. Evidence: scripts/evidence_checks.py, tests/test_evidence_checks.py, docs/benchmark-evidence-checks.md.

- [decision][refs:1][last_referenced:2026-10-12][last_verified:2026-10-12] v2.5 package retains v2.4 admission by default; final raw packet/literal policy is opt-in. Across96 paired workflow episodes, v2.5 aggregate tokens were1.73% lower but median end-to-end time1.43% higher; secondary adjudicated grounded facts were48/48 in every arm. No quality or speed superiority established. Strict scores and post-hoc adjudication remain separate. Evidence: docs/benchmark-v2.5.md and its public data.
- [constraint][refs:2][last_referenced:2026-10-13][last_verified:2026-10-13] All policies share source stat/descriptor guards, strict model candidate coordinates, and final rendered character cap; never roll these back with admission policy. Small inputs skip ranking/AST and reuse a bounded probe. Source changes withhold raw output and invalidate a just-written success report. Stat equality is not an atomic snapshot. Evidence: scripts/source_guard.py, scripts/router.py, tests/test_v25_boundaries.py.

## Warm Memory

- [decision][refs:1][last_referenced:2026-10-13][last_verified:2026-10-13] Preserve implicit selection requested by the user; narrow discovery to dispersed literal context instead of disabling implicit invocation. Dev14d742f adds explicit --search-context0..12 only with literal search; omitted defaults and shared safety remain unchanged. Narrower output can lose necessary evidence and is not semantic sufficiency. Evidence: tests/test_search_context.py, docs/token-value-review/report.ko.md.
- [measurement][refs:1][last_referenced:2026-10-13][last_verified:2026-10-13] Same4-task dev review:12 completed comparisons candidate80,343 vs plain127,478 tokens, strict25/25 vs24/25; actual reader used once at existing log width4, so gains are not isolated new-window effects. attrs costs+6.4%; retained timeout has unknown usage. All-attempt total tokens incomplete and candidate wall worsened. No stable/global promotion. Evidence: docs/token-value-review/summary.json and report.ko.md.

- [decision][refs:1][last_referenced:2026-10-13][last_verified:2026-10-13] Automatic discovery guidance now targets dispersed error logs; code/single-location lookup remains ordinary search. Metadata is not a hard host interceptor. No global update was authorized by a passed savings gate. Evidence: SKILL.md, agents/openai.yaml, docs/activation-gate-review/report.ko.md.
- [measurement][refs:1][last_referenced:2026-10-13][last_verified:2026-10-13] New implicit pilot8CLI: plain83,774 vs candidate105,459 tokens (+25.9%), both25/25 factual/visible-citation checks, observed skill reads/router0. All189,233 billed tokens known, no main timeout/retry; one post-call harness assembly failure reused its existing bill once. Stopped additional12 episodes and release/global promotion. Previous usage-unknown timeout remains unresolved history. Evidence: docs/activation-gate-review/summary.json.

## Cold Memory

## Archived Decisions
