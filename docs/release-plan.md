# 2.6.0 release candidate plan

Base: public v2.5.0/main 1737ae2. Prior experiment branch is preserved at 4ce8983; import only verified return-context modules/tests from 1a7c0a8. Historical 165 tests passed before branching. No experiment branch merge.

Default: Python-only tokens, v2.4 admission, shared safety, return-context off. B remains default because broad M benefit is unproven. Bounded Python return completion is optional; return-target implies bounded, explicit off conflicts. v2.5 admission stays optional.

Version 2.6.0: additive user-facing return options, managed installation and input limits justify minor release. Current public latest v2.5.0 verified via GitHub API; no tag/release publication authorized.

Target: Python 3.10–3.14, regular files on Linux/macOS/Windows; actual tested platforms listed separately. Optional cloud is advanced POSIX-only until process cleanup and live access are established; no default discovery/login/network.

Required: raw text/coordinates, source/final cap safety, managed install/update/rollback/uninstall, archive-only smoke, offline no-network tests, reproducible inventory, short self-contained skill, bounded mixed evaluation. CI configurations are not CI pass evidence.

Evaluation: freeze >=24 new tasks from >=8 public pinned independent sources before evaluating. Stress fixtures separate. Old examples are regression only. Actual skill/no-skill comparison max4 pairs/8 episodes, preflight1, CLI25, known350000tokens,600s monotonic,2 recovery/episode; same gpt-6.1-sol medium subscription and CLI0.162.1. Existing byte+16384 admission and240s pair reserve. Stop unknown usage/capacity/contract error; no retry/model/account change.

Publication boundary: produce archive/checksum/PR body/release draft/readiness; no main push/tag/GitHub release/global installation/AGENTS/auth changes.

Publication follow-up: the user subsequently authorized PR → CI → release → backed-up global installation. This initial plan remains historical; current results and CI evidence are in release-readiness.md.
