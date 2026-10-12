# Project Memory

## Hot Memory

- [decision][refs:2][last_referenced:2026-10-12][last_verified:2026-10-12] Default token optimization makes no selector-model call. Candidate admission uses rendered characters, not guaranteed total-token savings; whole read or targeted search is preferable when reduction is insufficient. Evidence: scripts/router.py, tests/test_token_priority.py, docs/benchmark-token-priority.md.
- [constraint][refs:2][last_referenced:2026-10-12][last_verified:2026-10-12] Preserve candidate boundary context before admission. Initial direct candidates lost cleanup evidence despite overlapping gold ranges; final regression measurements are72/72 with two-line neighbors and whole-read fallback. Evidence: docs/benchmark-v2.3.json. This is not a general completeness guarantee.

- [decision][refs:1][last_referenced:2026-10-12][last_verified:2026-10-12] Separate observable lexical anchors, syntax-boundary status, and packet admission. No matched query term in candidate cores triggers full reading or targeted search; this is not semantic absence or calibrated confidence. Python statement completion is bounded and can raise total tokens. Evidence: scripts/evidence_checks.py, tests/test_evidence_checks.py, docs/benchmark-evidence-checks.md.

- [decision][refs:1][last_referenced:2026-10-12][last_verified:2026-10-12] v2.5 package retains v2.4 admission by default; final raw packet/literal policy is opt-in. Across96 paired workflow episodes, v2.5 aggregate tokens were1.73% lower but median end-to-end time1.43% higher; secondary adjudicated grounded facts were48/48 in every arm. No quality or speed superiority established. Strict scores and post-hoc adjudication remain separate. Evidence: docs/benchmark-v2.5.md and its public data.
- [constraint][refs:1][last_referenced:2026-10-12][last_verified:2026-10-12] All policies share source stat/descriptor guards, strict model candidate coordinates, and final rendered character cap; never roll these back with admission policy. Small inputs skip ranking/AST and reuse a bounded probe. Source changes withhold raw output and invalidate a just-written success report. Stat equality is not an atomic snapshot. Evidence: scripts/source_guard.py, scripts/router.py, tests/test_v25_boundaries.py.

## Warm Memory

## Cold Memory

## Archived Decisions
