# Release readiness — 2.6.0

Decision: **B — basic local product is ready for review; optional cloud and automatic agent selection are not validated release guarantees.** Default is Python-only tokens, v2.4 policy, return-context off. Bounded return context and exact target filtering are explicit advanced local options. Publication and a backed-up global skill update are now authorized; they follow PR review and passing CI.

## Contract and scope

The release branch starts from public v2.5.0 `1737ae2`, not an experimental branch merge. Only verified return-context product changes/tests were imported from `1a7c0a8`. Package version, admission policy and product commit are separate. A deterministic archive pins the exact clean source commit and file SHA-256 inventory in release-manifest.json.

Validated runtime scope: macOS arm64, Python3.10 and3.14. Linux/Windows matrix is configured but has not executed for this branch; do not advertise those as tested. Core code is portable and default execution does not import resource or probe Codex. Cloud is POSIX-only compatibility behavior and no live Luna access was tested. Default use needs no model/login/network.

## Checks

| Gate | Result | Evidence |
|---|---|---|
| Historical pre-branch suite | PASS | 165 tests on preserved experiment branch |
| Current product regression | PASS | Full current suite, includes meaningful install/option/input regressions; see release validation summary |
| Existing manifest scenarios | PASS | 10 offline scenarios |
| Python3.10 /3.14 macOS | PASS | Local suites |
| Linux/Windows execution | NOT RUN | Prepared 6-job read-only CI matrix; no current-branch remote run |
| Default no network/model/subprocess | PASS | Forbidden socket/subprocess mocks; archive smoke uses empty PATH/no key |
| Input/output/source contracts | PASS | mutation, replacement, stale sidecar, FIFO, limits, coordinates, cap, Unicode/LF |
| POSIX selector child cleanup | PASS | Real local dummy process tree timeout; no model |
| Live Luna selector | NOT RUN | Not required or advertised for basic product |
| Managed install/update/restore/remove | PASS | Isolated paths, staged failure and swap rollback, edit/extra-file refusal |
| Runtime archive-only smoke | PASS | Clean commit archive, isolated examples/update/restore/uninstall; final checksums recorded separately |
| Installed skill discovery | PASS | Local Codex0.162.1 skills/list identified isolated repo skill; other skills disabled per invocation |
| Agent automatic selection | NOT RUN | No middleware/always-on claim |
| Fresh installed-skill paired model evaluation | PASS | Repaired harness completed 4 pairs/8 episodes; both arms4/4; tokens +10.65%, time +10.21%; no router calls |
| Mixed local evaluation | PASS | 24 new tasks /8 projects, default output identical to release baseline; no broader answer-quality claim |
| Global skill update | NOT RUN | Authorized after release; backup and hash verification required |
| Auth/AGENTS mutation | NOT APPLICABLE | Not needed for installation |
| Public GitHub tag/release | NOT RUN | Authorized; follows passing CI and PR merge |

## Fresh evaluation limitations

24 fixed questions from8 pinned independent projects: Python, JavaScript, Rust, logs and optional documentation;12 Korean/12 English. Original sources are downloaded separately and excluded from the distribution. Synthetic stresses and repeated queries are not independent real tasks. Default packets match baseline on24/24. Initial full-task evidence appears in20/24; the remaining4 need recovery or another allowed file. M activation changed0 of15 eligible mode tasks; target options were checked only when the question explicitly supplied a name. This is insufficient reason to default-enable return supplementation.

The actual installed-skill comparison completed four fixed pairs with gpt-6.1-sol/medium and Codex0.162.1 after the user explicitly authorized repairing the packet-only usage parser. Every episode used one ordinary search and cited visible source. Both arms4/4 correct/completed; no recovery/abstention/router calls. Plain54,756tokens/58.022s versus skill60,589tokens/63.946s: **no savings demonstrated**. Four pairs do not establish general equivalence or timing effects.

The first valid tool event had caused a harness failure, not an account/provider failure. Its raw usage and original result remain preserved. Including preflight and that unpaired call: **133,723known tokens,10CLI calls,137.505s**; all within the original budget. Cached/reasoning subsets were not re-added. Physical request counts/server hard caps are unobserved.

The measured installed SKILL matches final SKILL; its runtime came from873de65. A safe inventory-mismatch refusal prevented an intermediate installation update. Final runtime differs only in CLI UTF-8/LF configuration from that measured installation; the router never executed in those agent episodes. All five hashes and this distinction are recorded in repository evaluation data. Current local default packets were independently rechecked24/24 identical to baseline. This is not proof of automatic selection or routed recovery. Those paths and live Luna remain outside the validated basic-product guarantee.

## Publication and rollback

Keep the reviewed candidate archive/checksum/inventory together. Validate the pending CI platforms, publish the authorized branch/PR and exact tag/release. Do not attach historical savings to changed product hashes. Current publication state is also available on the GitHub release page.

Rollback with a verified installation backup, or a clean checkout/archive of public **v2.5.0 at1737ae2c360c1b495f627cf61f51b20f27ea806b**. Do not revert only an experimental return-context commit. Unmanaged old skill folders should be preserved and replaced manually after validating a new destination.
