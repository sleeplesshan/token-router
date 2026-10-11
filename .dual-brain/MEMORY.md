# Project Memory

## Hot Memory

- [decision][refs:1][last_referenced:2026-10-12][last_verified:2026-10-12] Default token optimization makes no selector-model call. Candidate admission uses rendered characters, not guaranteed total-token savings; whole read or targeted search is preferable when reduction is insufficient. Evidence: scripts/router.py, tests/test_token_priority.py, docs/benchmark-token-priority.md.
- [constraint][refs:1][last_referenced:2026-10-12][last_verified:2026-10-12] Preserve candidate boundary context before admission. Initial direct candidates lost cleanup evidence despite overlapping gold ranges; final regression measurements are72/72 with two-line neighbors and whole-read fallback. Evidence: docs/benchmark-v2.3.json. This is not a general completeness guarantee.

## Warm Memory

## Cold Memory

## Archived Decisions
