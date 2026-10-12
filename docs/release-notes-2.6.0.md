# Token Router 2.6.0

A local, standard-library Python CLI and agent skill for selecting relevant raw source lines. Default use needs no model, account or network.

- Safe default remains tokens/v2.4, with bounded return completion off.
- Optional `--return-context bounded` and explicit `--return-target QUALNAME` preserve existing context and can supplement short Python returns.
- Regular-file/resource limits, structured errors, source-change report invalidation, UTF-8/LF output and optional POSIX selector cleanup.
- Verified staged installation, update backups, restore, removal; deterministic archive and SHA-256 inventory.
- Small code/log/document samples and concise self-contained agent skill.

Minimum Python3.10. Validation: Linux/macOS/Windows GitHub CI with Python3.10/3.14, plus local macOS arm64Python3.10.20/3.14.5. Live cloud selection is an unvalidated advanced compatibility path, not part of the basic-product guarantee.

Performance: no universal token or latency promise. In four ordinary-search-sufficient tasks, explicit skill use answered4/4 but used10.65% more tokens. All opted for ordinary search. See repository evaluation rather than interpreting source-character reduction as total-token savings.

Migration: preserve unmanaged old skill folders. Install into a new destination, validate examples, then explicitly switch. Managed updates refuse modified/extra files or an unknown inventory; do not bypass that protection. Restore a verified backup or install public v2.5.0 from a clean checkout.

## Before public publication

- Review this branch and exact source commit; review archive manifest/SHA-256.
- Confirm the six Linux/macOS/Windows × Python3.10/3.14 jobs passed for the reviewed revision.
- Extract the reviewed archive in a fresh path and run the documented samples.
- Confirm no research sources, raw private prompts or credentials in the allowlisted artifact.
- Publication and global installation were authorized for this release; use the reviewed PR and passing CI.
- Publish the exact reviewed archive/checksum/inventory together; checksum is integrity, not publisher authentication.

Publication status and CI evidence are recorded in release-readiness.md and the GitHub release.
