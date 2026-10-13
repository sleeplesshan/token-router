# Release readiness — 2.8.0

Python3.10–3.14 standard-library local runtime. Linux/macOS/Windows basic CLI,
installer and stdio adapter are covered by the six-job offline CI matrix. Actual
Codex automatic selection/config connection was measured on macOS with CLI0.162.1;
Linux/Windows model-host operation, other main models and remote/multiroot hosts
remain unmeasured. No live Luna call or new selector model is part of validation.

| Check | Evidence |
|---|---|
| Local Python3.10/3.14 |217 unit tests,10 manifest scenarios; source/coordinate/output safety retained |
| MCP boundary |13 adapter tests: bounded transport, real reader, escape/type/source-change/timeout/error withholding |
| Installation |Known21→22file migration, exact rollback;7 ownership/policy tests and6 config-only RPC tests |
| Config integration |Temporary Codex homes: direct exposure CAS write, repeated connect/disconnect and unrelated configuration preserved; no main turns |
| Automatic real use |16main comparison + separately locked4code exclusions; positive tool4/4, negative0/6, guide0;50/50 factual+visible sufficient evidence,10/10 completed each arm |
| Costs |Eligible96953→73446tokens(−24.25%); exclusions117702→132074(+12.21%); combined214655→205520(−4.26%); whole wall121.63→124.15s(+2.07%) |
| All attempts |42known main turns,917402input+output; stopped candidates retained. No current usage-unknown or main timeout/retry observed |
| Packet ablation |All4actual MCP packets byte-identical UTF-8 output to existing guarded numbered CLI;5local repeats each; two source opens |
| CI/archive |Six PR/main jobs required; deterministic22file release archive and archive-only install/read/update/restore/remove smoke |
| Unmeasured |Fresh post-tuning independent holdout, workload prevalence, universal/per-task savings, other main models, unsupported formats, remote/multiroot automatic use |

Measured adapter/guide snapshot: package2.7.1 candidate commit4257adf, default
policyv2.4, gpt-6.1-sol medium, direct exposure. Code exclusion snapshotcb7c1cc
has the same adapter/guide/reader logic plus installer changes. Locks preserve
input/prompt/payload/client hashes. Release2.8.0 normalizes the CLI VERSION marker,forces MCP UTF-8 stdout on legacy locales (normal UTF-8 packets unchanged),
and documents validated installation; do not label past2.7.1 native host data as
measurements of this release. [Current report](automatic-tool-review/report.ko.md).

v2.4 remains default, v2.5 opt-in. Shared safety and CLI selection/ranking stay.
The installer changes only its destination and, with the connection option, the
owned MCP entry. Deployment of the maintainer's global instructions is a separate
recorded action, never implied by the repository release. Rollback disconnects
before restoring a verified21file backup/archive. Existing user edits are not reset.
