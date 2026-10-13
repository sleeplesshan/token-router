# Token Router

Retrieve bounded original lines from large Python files and logs before a reasoning model reads them. **Python-only by default: no model, login, network or source execution.** It returns evidence, not summaries or semantic confidence.

**v2.8.0 · Python3.10–3.14 · standard library · Linux/macOS/Windows.** [Support and validation](docs/release-readiness.md).

## Install

```sh
git clone --branch v2.8.0 --depth 1 https://github.com/sleeplesshan/token-router.git
cd token-router
python3 scripts/install.py install --dest "$HOME/.agents/skills/token-router" --connect-codex
python3 "$HOME/.agents/skills/token-router/scripts/router.py" --version
```

Or download the versioned archive and SHA-256 from [Releases](https://github.com/sleeplesshan/token-router/releases), verify it, extract it and run its installer. A checksum verifies integrity, not publisher identity. Use a reviewed pinned source. Windows PowerShell: use `python` and `--dest "$env:USERPROFILE/.agents/skills/token-router"`. Only22 allowlisted runtime/support files are installed; research sources, raw events and benchmark tools are excluded. An unmanaged copied installation is never overwritten; install to a new destination first.

## Choose the smallest adequate read

Use ordinary search for a literal answer or an already-known short range. Reuse visible evidence. The connected `read_pytest_failures` tool can be selected automatically for comparisons of multiple named pytest failure blocks and distant results, when visible evidence is insufficient. Complete Python callable retrieval remains an explicit manual capability. File size alone does not make it worthwhile.

```sh
# Complete explicitly named callables, batched; no dependency traversal.
python3 scripts/router.py heavy_code path/to/module.py \
  --symbol Store.lookup --symbol helper --line-numbers --compact-status

# Exact failure-header fragments and a dispersed summary, batched.
python3 scripts/router.py error_log path/to/ci.log \
  --search-term 'ERROR: worker (' --search-term 'Total test files:' \
  --activation-profile log-context --line-numbers --compact-status

# Existing general query path: default local tokens / v2.4 policy.
python3 scripts/router.py heavy_code samples/service.py --query retry_delay
python3 scripts/router.py agent_context samples/reference.md --query rollback
```

Resolve the script relative to the installed skill, not the current project. The recommended install command also registers one local, read-only Codex MCP tool and exposes its compact schema directly. **Start a new Codex session after installing/updating or changing the connection.** Ordinary log questions need no `$token-router` invocation or guide read. The model chooses whether to use the tool; installation does not intercept every file read.

Codex CLI is needed for connection (tested0.162.1). Existing installations can run `python3 scripts/install.py connect-codex --dest "$HOME/.agents/skills/token-router"`. CLI-only installation can omit `--connect-codex`; it needs only Python. If connection fails, the verified local installation remains and the installer reports a reconnect action. [Connection, scope and removal](docs/activation-integration.md). [Claude Code](CLAUDE.md) supports the same manual CLI; its automatic path was not measured.

## What is returned

`--symbol QUALNAME` selects1–8 unique functions/async methods, including decorators, in Python up to1,000,000 decoded characters. Nested/overlapping definitions merge. Missing/duplicate names, invalid syntax or an oversized batch withhold the entire output. Complete definitions do not include dependencies or enclosing runtime conditions.

`--search-term TEXT` is repeated, case-sensitive substring selection. Logs match ANSI-SGR-stripped text while preserving the original lines. Default neighbors: logs4, code12; `--search-context 0..12` explicitly changes only this path. Selected recognizable Python/pytest failure blocks can extend to their end marker within64 lines. All formats and complete dependencies are not promised. Prefer distinctive headers over frequent bare test names.

Both explicit readers cap their whole rendered packet at12,000 characters plus the common output limit; they never silently cut a function or window. `--line-numbers` labels the original1-based lines. `--compact-status` reduces stderr presentation, preserving useful failure coordinates; `--report-json PATH` retains detailed diagnostics. Verify that the returned lines actually support each claim and read only missing context.

| Status / exit | Meaning |
|---|---|
| auto_full /0 | Whole decoded source |
| auto_candidates /0 | Excerpt; verify evidence |
| needs_targeted_read /2 | Empty source output; narrow or read specific ranges |
| bypass /2 | Profile rejected; ordinary targeted search, empty source output |
| usage_error /2 | Correct the command |
| error /1 | Input, source change or report failure; empty source output |
| fallback /0 | Optional selector failed; inspect model_failed |

The general query policy remains **v2.4**, with **v2.5 opt-in**; return-context remains off. Optional `--return-context bounded`/`--return-target QUALNAME` are separate existing features. Shared stat/path+descriptor checks, strict model-visible coordinates and final rendered output cap remain in every path. Metadata checks are not atomic snapshots. UTF-8 replacement and LF normalization preserve decoded lines, not exact original bytes. [Complete CLI contract](references/contract.md).

## Automatic selection and measured costs

The native tool uses the existing `log-context` profile and all common safety checks. It is scoped to multiple named pytest failure blocks plus distant results; code, a single traceback, literal lookups and sufficient visible evidence use ordinary search. Its immutable read root follows the local Codex session's startup workspace. No selector model, source execution, network, embeddings or persistent read history is added. The general default policy remains v2.4, optional v2.5.

A text-only comparison with the installed skill and connected tool made4/4 actual automatic calls on eligible log episodes and0/6 on excluded episodes, with no guide loading or forced tool choice. The16-episode main trial plus separately locked4-episode code exclusion check used gpt-6.1-sol medium and known/development sources; this is not an independent new-project holdout.

| Measure | Ordinary search | Installed + connected |
|---|---:|---:|
| Answers with sufficient visible evidence |50/50|50/50|
| Eligible logs total input + output |96,953|73,446 (−24.25%)|
| Excluded tasks total input + output |117,702|132,074 (+12.21%)|
| Combined20-episode input + output |214,655|205,520 (−4.26%)|
| Combined whole wall sum |121.63s|124.15s (+2.07%)|
| Automatic calls: logs / exclusions |0 /0|4/4 /0/6|

![Automatic local tool comparison](https://raw.githubusercontent.com/sleeplesshan/token-router/v2.8.0/docs/automatic-tool-review/comparison.png)

**Observed log savings do not guarantee a saving on every task or workload.** Direct schema exposure has context cost even when the tool is skipped; excluded tasks increased in this sample. SymPy logs saved9.77% tokens with slower completion; SciPy saved34.30%. General speed improvement is unproven. A short-answer-heavy workload may be better with this connection disabled. [Full paired data, failed candidates, ledger, hashes and reproduction](docs/automatic-tool-review/report.ko.md).

All42 main turns in this development work cost917,402 known input+output tokens, including stopped candidates. Final comparison cost420,175; no unknown usage, main timeout or retry occurred. Cache/reasoning subsets are not added twice. Earlier cold-guide and non-selection failures remain in the report; their measurements are not reused as successful release evidence. The character margin remains a heuristic. Use sufficient context for broad/cross-file work and never route mandatory instructions.

## Update, restore, remove

Run the new reviewed checkout/archive's installer. It verifies existing managed hashes, refuses edits/extras/symlinks, validates staging and prints a backup location outside skill discovery.

```sh
python3 scripts/install.py update --dest "$HOME/.agents/skills/token-router"
python3 scripts/install.py verify --dest "$HOME/.agents/skills/token-router"
python3 scripts/install.py disconnect-codex --dest "$HOME/.agents/skills/token-router"
python3 scripts/install.py restore --dest "$HOME/.agents/skills/token-router" --backup /verified/backup
python3 scripts/install.py uninstall --dest "$HOME/.agents/skills/token-router" --connect-codex
```

The connection option changes only the owned `token-router` MCP entry; CLI-only installation leaves Codex configuration unchanged. Other skills, AGENTS, model and auth are untouched by the installer. Keep personal edits separately. Disconnect before restoring a21-file release (v2.7.1 or earlier). Backups preserve exact payload inventories; existing changed MCP settings are never silently removed.

## Development / advanced use

```sh
python3 -m unittest discover -s tests
python3 scripts/run_router_tests.py tests/router-tests.json
python3 scripts/build_release.py --output dist
python3 scripts/smoke_archive.py dist/token-router-2.8.0.zip
```

These checks are offline and make no model call. Optional cloud/legacy latency selection is an advanced POSIX compatibility path using fixed `gpt-6-luna`/low via Codex login. It is never automatic, not required, and live Luna access is unvalidated for this release. Your main agent can separately send the extracted evidence to its own model.

[CONTRIBUTING](CONTRIBUTING.md) · [SUPPORT](SUPPORT.md) · [SECURITY](SECURITY.md) · [MIT license](LICENSE). Public samples are synthetic; third-party benchmark material has [separate provenance/notices](https://github.com/sleeplesshan/token-router/blob/v2.7.0/docs/actual-reader-review/SOURCES.md).
