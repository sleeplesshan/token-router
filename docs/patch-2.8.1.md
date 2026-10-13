# Scoped Codex registration —2.8.1

## Problem and patch

Codex0.162.1 `mcp add/remove` rebuilds the MCP server map, serializing every
existing entry. Unrelated integer timeouts may become floats and empty/default
settings may disappear.2.8.0 used those commands for creation/removal even though
its exposure write was scoped. This violated the intended narrow write boundary.

2.8.1 uses `config/value/write` only for the owned `mcp_servers.token-router`
table (creation/deletion) or its exposure key (matching existing connection).
The user-layer `filePath` and `expectedVersion` implement compare-and-swap
for semantic configuration changes. Comment-only edits do not change that version;
the scoped edit preserves them. This is not a byte snapshot or arbitrary-edit lock.
Changed/foreign registrations are preserved; rollback removes only the exact
registration created by this attempt. `codex mcp get` remains read-only.
No config contents/authentication values are printed or included in reports.

Primary implementation checked: official Codex0.162.1
[map serialization](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/core/src/config/edit.rs#L463),
[server serialization](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/core/src/config/edit/document_helpers.rs#L132).

## Scope and evidence identity

Reader selection, schema/instructions, setup skill and MCP packet extraction are
unchanged. The only reader-file change is `VERSION = "2.8.1"`. Default policyv2.4,
optionalv2.5,15% character margin and common safety contracts remain.
No new model trial was run for this installer patch. The measured20episodes and
42-turn development ledger remain at their original commits/hashes and rubric
versions in [the frozen report](automatic-tool-review/report.ko.md).

Those measurements show50/50 grounded fact conditions per arm, actual log tool
calls4/4, exclusions0/6, logs−24.25%total tokens, exclusions+12.21%, combined−4.26%,
whole wall+2.07%. They are development/regression evidence, not universal savings
or an independent post-tuning holdout. They must not be labeled new2.8.1 model runs.

## Offline verification

Python3.10 and3.14 each passed221 unit tests (one platform-specific skip), plus
10manifest scenarios. The17 connection/config tests include the real temporary
home checks described below. All42 original main turns and917,402known total
tokens reconcile from frozen raw events without another model call.
[Reader/schema/guide identity](patch-2.8.1-identity.json) confirms eight files are
unchanged from release commit6638817 except the router VERSION marker.

## Reproduction and rollback

```sh
python3 -m unittest discover -s tests
python3 scripts/run_router_tests.py tests/router-tests.json
python3 docs/automatic-tool-review/verify_evidence.py
python3 scripts/build_release.py --output /tmp/token-router-2.8.1-release
python3 scripts/smoke_archive.py /tmp/token-router-2.8.1-release/token-router-2.8.1.zip
```

Config-only tests with Codex installed use a temporary `CODEX_HOME`, never start
threads/models, and check scoped creation/exposure/deletion, stale versions and
preservation of unrelated comments, timeout types and empty settings. CI hosts
without Codex skip the live config-only case and still exercise mocked contracts.

Update from the reviewed archive/checkout with `scripts/install.py update --dest
/installed/token-router --connect-codex`. Installation and connection failures are
reported separately. Start a new Codex session after any connection/payload change.
Restore a verified22-file backup with the same installer; disconnect first for an
older21-file payload. Never reset unrelated config to an older whole-file backup.
