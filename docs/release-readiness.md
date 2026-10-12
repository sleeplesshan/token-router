# Release readiness — 2.6.0 candidate

Decision: **B — basic local product is ready for review; optional cloud and automatic agent selection are not validated release guarantees.** Default is Python-only tokens, v2.4 policy, return-context off. Bounded return context and exact target filtering are explicit advanced local options. No main push, public tag/release or global installation was performed.

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
| Runtime archive-only smoke | NOT RUN | Final artifact validation recorded before publication |
| Installed skill discovery | PASS | Local Codex0.162.1 skills/list identified isolated repo skill; other skills disabled per invocation |
| Agent automatic selection | NOT RUN | No middleware/always-on claim |
| Fresh installed-skill paired model evaluation | NOT RUN | Stopped after preflight and one unpaired ordinary-search episode: harness contract mismatch |
| Mixed local evaluation | PASS | 24 new tasks /8 projects, default output identical to release baseline; no broader answer-quality claim |
| Global install/auth/AGENTS mutation | NOT APPLICABLE | Explicitly outside scope |
| Public GitHub tag/release | NOT RUN | Requires separate approval |

## Fresh evaluation limitations

24 fixed questions from8 pinned independent projects: Python, JavaScript, Rust, logs and optional documentation;12 Korean/12 English. Original sources are downloaded separately and excluded from the distribution. Synthetic stresses and repeated queries are not independent real tasks. Default packets match baseline on24/24. Initial full-task evidence appears in20/24; the remaining4 need recovery or another allowed file. M activation changed0 of15 eligible mode tasks; target options were checked only when the question explicitly supplied a name. This is insufficient reason to default-enable return supplementation.

The actual agent run used gpt-6.1-sol/medium, Codex0.162.1, existing ChatGPT auth, read-only tools and an installed isolated skill. It did not use the old skills-disabled packet-replay contract as proof of skill behavior. Unfortunately its reused usage parser rejected the first valid command_execution event. The run stopped without retry as required. Raw usage was present: preflight6084 + unpaired ordinary-search12294 = **18378 known tokens**, two CLI invocations,15.499s. The original stopped ledger is preserved; a separate correction restores known usage. No paired token/time/quality effect can be computed. Tool-enabled accounting was then fixed and regression-tested without another model call. Do not label this an account capacity failure or missing provider usage.

The unpaired ordinary-search answer was correct and cited the actual returned line. It is not compared against an unexecuted skill arm. Automatic skill decisions, real follow-up behavior on changed sources/missing files, and new total-token savings remain unmeasured. Installation discovery and local router tests are different evidence.

## Publication and rollback

Keep the reviewed candidate archive/checksum/inventory together. After approval, validate the pending CI platforms, publish the reviewed branch/PR and exact approved tag/release. Do not attach historical savings to changed product hashes. No new release was published by this task.

Rollback with a verified installation backup, or a clean checkout/archive of public **v2.5.0 at1737ae2c360c1b495f627cf61f51b20f27ea806b**. Do not revert only an experimental return-context commit. Unmanaged old skill folders should be preserved and replaced manually after validating a new destination.
