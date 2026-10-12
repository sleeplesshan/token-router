# Release readiness — v2.7.0

Local explicit extraction is ready; publication requires the current PR's six-job CI. Default remains Python-only tokens, v2.4 admission and return-context off. v2.5 is opt-in. No auto cloud, local inference, embeddings or recovery engine. Optional Luna compatibility is not live-validated.

## Checks and evidence

| Gate | Current evidence |
|---|---|
| Offline suite |181 tests on macOS Python3.10.20/3.14.5; platform skips explicit |
| Existing manifest |10/10 scenarios |
| Shared safety |Source mutation/replacement, strict visible model coordinates, output/input caps, long lines, report failures, zero default model calls and CLI priority remain tested |
| New readers |Complete decorators/async/nested targets, ambiguity/missing/syntax/whole-batch caps, one guarded probe, selected pytest block, compact stdout/sidecar identity, bounded ambiguity |
| Default regression |24 mixed tasks /8 pinned projects match publicv2.6.0 atf68dc09 with defaultv2.4 query policy; optional new selectors are separate |
| Archive lifecycle |Install/read-only source/update/restore/uninstall from isolated Unicode/space paths with empty PATH/no key; symbol/literal/numbering smoke |
| Cross-platform execution |Required: Linux/macOS/Windows × Python3.10/3.14 current PR CI; publication gate, not inferred from local tests |
| Native installed-skill comparison |16 episodes, actual router8/8, fixed-rubric48/48 both arms, completion8/8 both; total tokens-18.23% and observed wall sum-3.86% |
| Automatic selection / cold implicit |Not established. Earlier cold CLI delivery increased tokens24.12%; no middleware guarantee |
| Main timeout/cost capture |All48 new main turns have complete usage; no timeout/retry. Final16 native counters/command counts reconciled against ordered raw events |
| Cloud/other models/new project holdout |Not run; not a basic product requirement |
| Global installation |Verified separately by local installer backup/hash receipt after publication; a GitHub release alone does not change a machine |

## Version and measurement separation

Stable predecessor: v2.6.0 atf68dc09bab5c331034feff4137bf91f41a36e880. The final real-use measurement pins package2.7.0 candidate/commit3ad145c, unchanged defaultv2.4 policy, exact user prompt/source/guide/runtime hashes and gpt-6.1-sol medium. Released runtime and guide hashes must match those measured paths; later documentation/research provenance commits are identified separately by the release manifest. No past benchmark is relabeled as a new model run.

[Actual-reader report](actual-reader-review/report.ko.md), [ledger](actual-reader-review/episodes.json), [native raw audit](actual-reader-review/native-audit.json), [execution lock](actual-reader-review/run-native-lock.json), [source notices](actual-reader-review/SOURCES.md).

The four development tasks use known public code/log families; repeats are not independent projects. Pandas savings are negligible and one repeat increases tokens. CPython token savings coexist with21.47% longer time. Overall timing is descriptive; remote wait cannot be isolated from wall-minus-child-CPU. Default query output preservation does not imply every new literal output matches old literal behavior: selected failure completion intentionally adds evidence.

Original gold/scores and independent source-coordinate/format adjudication remain separate. Native criteria were fixed before native calls. The research client has latent failure-path notification risks; all16 completed native traces were independently reconciled, not a universal client validation. All48 new turns total1,050,651known tokens within1.1M/50-turn budget. Historical usage-unknown timeout remains unknown and separate.

## Publication and rollback

Create reviewed PR, wait for all six CI jobs, merge that head, tagv2.7.0, build/download/verify the deterministic archive and SHA inventory, then update the managed global installation with backup/hash verification. Research sources and events are not in the21-file installed payload. Never edit authentication or global AGENTS as a side effect.

Rollback to a verifiedv2.6.0 archive/tag or the validated backup printed by the installer. Do not reset user work, bypass managed-edit checks, or remove shared safety when changing an admission policy. Unsupported metadata detection fails closed; stat equality is not an atomic snapshot.
