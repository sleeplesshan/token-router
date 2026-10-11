# Project Memory

## Hot Memory

- [decision][refs:2][last_referenced:2026-10-12][last_verified:2026-10-12] Default token optimization makes no selector-model call. Candidate admission uses rendered characters, not guaranteed total-token savings; whole read or targeted search is preferable when reduction is insufficient. Evidence: scripts/router.py, tests/test_token_priority.py, docs/benchmark-token-priority.md.
- [constraint][refs:2][last_referenced:2026-10-12][last_verified:2026-10-12] Preserve candidate boundary context before admission. Initial direct candidates lost cleanup evidence despite overlapping gold ranges; final regression measurements are72/72 with two-line neighbors and whole-read fallback. Evidence: docs/benchmark-v2.3.json. This is not a general completeness guarantee.

- [decision][refs:1][last_referenced:2026-10-12][last_verified:2026-10-12] Separate observable lexical anchors, syntax-boundary status, and packet admission. No matched query term in candidate cores triggers full reading or targeted search; this is not semantic absence or calibrated confidence. Python statement completion is bounded and can raise total tokens. Evidence: scripts/evidence_checks.py, tests/test_evidence_checks.py, docs/benchmark-evidence-checks.md.

## Warm Memory

## Cold Memory

## Archived Decisions
