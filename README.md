# Token Router

Retrieve bounded original lines from large Python files and logs before a reasoning model reads them. **Python-only by default: no model, login, network or source execution.** It returns evidence, not summaries or semantic confidence.

**v2.7.1 · Python3.10–3.14 · standard library · Linux/macOS/Windows.** [Support and validation](docs/release-readiness.md).

## Install

```sh
git clone --branch v2.7.1 --depth 1 https://github.com/sleeplesshan/token-router.git
cd token-router
python3 scripts/install.py install --dest "$HOME/.agents/skills/token-router"
python3 "$HOME/.agents/skills/token-router/scripts/router.py" --version
```

Or download the versioned archive and SHA-256 from [Releases](https://github.com/sleeplesshan/token-router/releases), verify it, extract it and run its installer. A checksum verifies integrity, not publisher identity. Use a reviewed pinned source. Windows PowerShell: use `python` and `--dest "$env:USERPROFILE/.agents/skills/token-router"`. Only21 allowlisted runtime/support files are installed; research sources, raw events and benchmark tools are excluded. An unmanaged copied installation is never overwritten; install to a new destination first.

## Choose the smallest adequate read

Use ordinary search for a literal answer or an already-known short range. Reuse visible evidence. Automatic scope is limited to dispersed recognizable failure blocks plus distant result context, with native guide delivery and insufficient visible evidence. Complete Python callable retrieval remains an explicit manual capability. File size alone does not make it worthwhile.

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

Resolve the script relative to the installed skill, not the current project. `$token-router` works with skill-capable hosts; [SKILL.md](SKILL.md) gives the retrieval instructions. Prefer a host that supplies the guide before execution, and never read it again when already provided. Plain text naming a skill is not necessarily native skill injection: the validated Codex path uses its registered skill input. [Claude Code](CLAUDE.md) can use the same local CLI manually. Automatic discovery is guidance dependent on the host, not middleware that intercepts every read.

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

## Conservative activation and measured limits

A connected host can call `routing_policy.plan_activation` **before native skill injection** using already-known context needs, selectors and visible-evidence state. Code, simple lookups, one selector, sufficient evidence and cold delivery bypass. The optional `--activation-profile log-context` then checks actual dispersion and bounded failure context during the existing reader scan, without another file pass or model turn. It never falls back to whole source on rejection. [Host integration contract](https://github.com/sleeplesshan/token-router/blob/v2.7.1/docs/activation-integration.md).

**Installation alone does not connect this host gate or intercept all reads.** Metadata narrows discovery; connected execution enforces attachment/bypass. Manual CLI without the profile and default query policy remain unchanged. Admission is a conservative heuristic, not a guarantee against efficient batched search.

A16-episode native regression trial compared ordinary search with the connected gate on2 dispersed logs and2 excluded tasks, each repeated twice. The measured candidate was package2.7.0/e3b5217;2.7.1 retains its runtime logic and guide with version/docs/test updates. Model: gpt-6.1-sol medium, no selector call.

| Measure | Ordinary search | Connected gate |
|---|---:|---:|
| Fixed-rubric answers + evidence, actual logs |24/24|24/24|
| Actual logs input + output |112,242|82,143 (−26.82%)|
| Actual logs whole wall sum |42.76s|54.50s (+27.46%)|
| Router/profile calls on admitted logs |0|4/4|
| Skill attachment/guide read/router on exclusions |0|0/4|
| All answers + evidence |38/38|38/38|
| All input + output |162,608|133,954 (−17.62%)|
| All whole wall sum |85.96s|104.04s (+21.03%)|

![Conservative activation comparison](https://raw.githubusercontent.com/sleeplesshan/token-router/v2.7.1/docs/conservative-activation-review/comparison.png)

This is an **optional token-saving log path, with slower observed completion**. CPython saved19.51% tokens; SciPy33.13%, but SciPy time increased. Excluded paths had identical prompts/native inputs and ordinary retrieval; their2.87% token variation is not gate savings or gate execution cost. All16 turns cost296,562 known tokens; no failures/timeouts or unknown usage occurred. Rejected admissions and failures would count, with unknown usage stopping the trial. [Full results, hashes, packets and raw events](https://github.com/sleeplesshan/token-router/blob/v2.7.1/docs/conservative-activation-review/report.ko.md).

Known-source regression evidence is not a new project holdout or universal per-task guarantee. Previous [v2.7 explicit-reader evaluation](https://github.com/sleeplesshan/token-router/blob/v2.7.0/docs/actual-reader-review/report.ko.md) retained native savings and cold24.12% losses; code savings ranged from substantial to negligible. The15% general rendered-character margin remains unchanged. Defaultv2.4 and optionalv2.5 retain their original safety and evidence contracts. Use complete context for broad/cross-file work and never route mandatory instructions.

## Update, restore, remove

Run the new reviewed checkout/archive's installer. It verifies existing managed hashes, refuses edits/extras/symlinks, validates staging and prints a backup location outside skill discovery.

```sh
python3 scripts/install.py update --dest "$HOME/.agents/skills/token-router"
python3 scripts/install.py verify --dest "$HOME/.agents/skills/token-router"
python3 scripts/install.py restore --dest "$HOME/.agents/skills/token-router" --backup /verified/backup
python3 scripts/install.py uninstall --dest "$HOME/.agents/skills/token-router"
```

It does not change AGENTS, other skills, model configuration or auth. Keep personal edits separately. Roll back with a verifiedv2.7.0 archive/tag or the installation backup.

## Development / advanced use

```sh
python3 -m unittest discover -s tests
python3 scripts/run_router_tests.py tests/router-tests.json
python3 scripts/build_release.py --output dist
python3 scripts/smoke_archive.py dist/token-router-2.7.1.zip
```

These checks are offline and make no model call. Optional cloud/legacy latency selection is an advanced POSIX compatibility path using fixed `gpt-6-luna`/low via Codex login. It is never automatic, not required, and live Luna access is unvalidated for this release. Your main agent can separately send the extracted evidence to its own model.

[CONTRIBUTING](CONTRIBUTING.md) · [SUPPORT](SUPPORT.md) · [SECURITY](SECURITY.md) · [MIT license](LICENSE). Public samples are synthetic; third-party benchmark material has [separate provenance/notices](https://github.com/sleeplesshan/token-router/blob/v2.7.0/docs/actual-reader-review/SOURCES.md).
