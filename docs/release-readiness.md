# Release readiness — 2.6.0

Decision: **B — basic local product is ready for publication; optional cloud and automatic agent selection are not validated release guarantees.** Default is Python-only tokens, v2.4 policy, return-context off. Bounded return context and exact target filtering are explicit advanced local options. The reviewed release is published through PR #1. Machine-specific backup/install receipts are kept locally rather than embedded in the portable artifact.

## Contract and scope

The release branch starts from public v2.5.0 `1737ae2`, not an experimental branch merge. Only verified return-context product changes/tests were imported from `1a7c0a8`. Package version, admission policy and product commit are separate. A deterministic archive pins the exact clean source commit and file SHA-256 inventory in release-manifest.json.

Validated basic runtime scope: Linux, macOS and Windows, Python3.10 and3.14, through the six-job GitHub Actions matrix. Intermediate Python versions are expected compatible, not individually tested. Core code is portable and default execution does not import resource or probe Codex. Cloud is POSIX-only compatibility behavior and no live Luna access was tested. Default use needs no model/login/network.

## Checks

| Gate | Result | Evidence |
|---|---|---|
| Historical pre-branch suite | PASS | 165 tests on preserved experiment branch |
| Current product regression | PASS | 147 collected tests; platform-specific skips for POSIX transport/FIFO and Windows refusal; includes install/input regressions |
| Existing manifest scenarios | PASS | 10 offline scenarios |
| Python3.10 /3.14 macOS | PASS | Local suites |
| Linux/macOS/Windows execution | PASS | [Six-job CI](https://github.com/sleeplesshan/token-router/actions/runs/38256738861), Python3.10 and3.14, includes archive smoke |
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
| Machine-specific global installation | NOT APPLICABLE | Portable artifact does not assert installation state; local backup/hash receipt verifies deployment |
| Auth/AGENTS mutation | NOT APPLICABLE | Not needed for installation |
| Publication state | NOT APPLICABLE | Verify published tag and assets on the GitHub release page; not a runtime test |

## Fresh evaluation limitations

24 fixed questions from8 pinned independent projects: Python, JavaScript, Rust, logs and optional documentation;12 Korean/12 English. Original sources are downloaded separately and excluded from the distribution. Synthetic stresses and repeated queries are not independent real tasks. Default packets match baseline on24/24. Initial full-task evidence appears in20/24; the remaining4 need recovery or another allowed file. M activation changed0 of15 eligible mode tasks; target options were checked only when the question explicitly supplied a name. This is insufficient reason to default-enable return supplementation.

The actual installed-skill comparison completed four fixed pairs with gpt-6.1-sol/medium and Codex0.162.1 after the user explicitly authorized repairing the packet-only usage parser. Every episode used one ordinary search and cited visible source. Both arms4/4 correct/completed; no recovery/abstention/router calls. Plain54,756tokens/58.022s versus skill60,589tokens/63.946s: **no savings demonstrated**. Four pairs do not establish general equivalence or timing effects.

The first valid tool event had caused a harness failure, not an account/provider failure. Its raw usage and original result remain preserved. Including preflight and that unpaired call: **133,723known tokens,10CLI calls,137.505s**; all within the original budget. Cached/reasoning subsets were not re-added. Physical request counts/server hard caps are unobserved.

The measured installed SKILL matches final SKILL; its runtime came from873de65. A safe inventory-mismatch refusal prevented an intermediate installation update. The measured installation predates CLI UTF-8/LF configuration and the release CI fix for native Windows change-time metadata; the router never executed in those agent episodes. All five hashes and this distinction are recorded in repository evaluation data. Local default packets were independently rechecked24/24 identical to baseline before the Windows-only metadata fix. The fix preserves POSIX identity checks and adds no model calls. This is not proof of automatic selection or routed recovery. Those paths and live Luna remain outside the validated basic-product guarantee.

## Publication and rollback

Keep the reviewed candidate archive/checksum/inventory together. CI validates the supported platform matrix; publication uses the reviewed PR and exact tag/commit. Do not attach historical savings to changed product hashes. Current publication state is also available on the GitHub release page.

Rollback with a verified installation backup, or a clean checkout/archive of public **v2.5.0 at1737ae2c360c1b495f627cf61f51b20f27ea806b**. Do not revert only an experimental return-context commit. Unmanaged old skill folders should be preserved and replaced manually after validating a new destination.

## CI compatibility correction

Initial Windows CI exposed POSIX transport tests running against the deliberately disabled Windows cloud path, open-file deletion assumptions, and Windows stat ctime being creation time. The release reads native ChangeTime for Windows path/descriptor checks; API failure is closed. Mutation tests remain enabled, with Windows open-handle locking tested explicitly. Optional cloud transport cases are POSIX-only and Windows refusal is tested. [Microsoft FILE_BASIC_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_basic_info). The process-tree timeout fixture allows three seconds for process startup; runtime timeout defaults are unchanged.

A later Windows CI repeat exposed same-tick timestamp resolution in the restored-mtime fixture. The fixture now waits50ms before a write to exercise an actual changed timestamp. The product does not sleep or claim atomic snapshot detection: same-tick/restored-metadata limitations are explicitly documented in the contract and security guide.
