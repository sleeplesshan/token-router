# Token Router

Retrieve original, numbered line ranges from large code files, logs and optional references before a reasoning model reads them. **Python-only by default: no Codex, login, model or network request required.** It selects evidence; it does not summarize, execute code, prove completeness, or guarantee token/time savings.

**2.6.0**. Python **3.10–3.14**, standard library. Basic CLI is CI-tested on Linux/macOS/Windows with Python3.10 and3.14; actual validation and optional-feature limits are recorded in [release readiness](docs/release-readiness.md). Optional cloud selection has a narrower advanced support contract.

## Install and first use

```sh
git clone --branch v2.6.0 --depth 1 https://github.com/sleeplesshan/token-router.git
cd token-router
```

Use a reviewed checkout or verify the SHA-256 beside a downloaded release archive before extracting it. A checksum detects changes; it does not authenticate the publisher. Download the versioned archive and checksum from [Releases](https://github.com/sleeplesshan/token-router/releases). From its extracted directory:

```sh
python3 scripts/install.py install --dest "$HOME/.agents/skills/token-router"
python3 "$HOME/.agents/skills/token-router/scripts/router.py" --version
python3 "$HOME/.agents/skills/token-router/scripts/router.py" --help
python3 "$HOME/.agents/skills/token-router/scripts/router.py" heavy_code "$HOME/.agents/skills/token-router/samples/service.py" --query retry_delay
python3 "$HOME/.agents/skills/token-router/scripts/router.py" error_log "$HOME/.agents/skills/token-router/samples/incident.log" --query payment_timeout
python3 "$HOME/.agents/skills/token-router/scripts/router.py" agent_context "$HOME/.agents/skills/token-router/samples/reference.md" --query rollback
```

Windows: use `python` and an absolute destination such as `"$env:USERPROFILE/.agents/skills/token-router"` in PowerShell. The installer accepts any explicit isolated destination; no administrator permissions are needed. Download/checkout uses network; the installed default router does not. Only the allowlisted runtime, skill, samples and support documents are installed; no benchmark logs or raw prompts.

For reproducible source installation check out the exact tag/commit shown in `release-manifest.json`. Do not run an unreviewed remote script through a shell. An old unmanaged `cp -R` installation is never overwritten: install in a new destination, then replace it manually after inspection.

## CLI or agent skill

The commands above work from any directory. With a skill-capable agent, invoke `$token-router` and provide the source and question. The installed [SKILL.md](SKILL.md) resolves its own script path. Automatic selection is allowed, but this is guidance—not middleware that intercepts every read. No private global AGENTS setup is required. Agent-specific automatic discovery is validated separately from CLI extraction; see readiness. Claude Code users can follow [CLAUDE.md](CLAUDE.md) manually.

Prefer ordinary search and nearby raw lines for exact symbols. Reuse already-read evidence. Small files are read whole. Use routing when a focused task still has too much context; use full necessary context for audits and cross-file dependency work. Never route mandatory security/permission/AGENTS instructions away.

## Understand the result

| stderr status | Meaning / next step |
|---|---|
| auto_full | All decoded source returned |
| auto_candidates | Raw excerpt; verify it supports the answer |
| needs_targeted_read (exit2) | No raw output; narrow search or inspect specific ranges/files |
| usage_error (exit2) | Correct the command |
| error (exit1) | Fix input, source change, or diagnostic write failure |
| fallback | Optional selector failed; local evidence only, not selector success |

Exit0 is extraction success, not answer correctness. The default policy is **v2.4**, with all shared source/coordinate/output safety checks. v2.5 final-packet admission remains opt-in. Candidates must fit the budget and shrink rendered characters by15%; this is a heuristic, not a measured token break-even. UTF-8 decoding replaces invalid bytes and normalizes CRLF/CR to LF. No byte-for-byte claim is made.

## Optional Python return context

```sh
python3 scripts/router.py heavy_code path/to/module.py --query lookup --return-context bounded
python3 scripts/router.py heavy_code path/to/module.py --query 'What does lookup return? Target: Store.lookup.' --return-target Store.lookup
```

Default return-context is **off**. `bounded` can add short sole Returns after selected docstring-only function headers without dropping existing lines. `return-target` implies bounded and limits incidental additions to one exact AST name/qualname; ambiguous/unresolved targets keep bounded output. Explicit off+target is an error. No receiver inference or query-intent model is used. These options require local tokens, heavy_code, focused scope; v2.5 policy is independent.

The [full contract](references/contract.md) covers options, report schema, resource caps, environment variables and migration details. Regular inputs are bounded to64MiB/250000lines/1000000decoded characters per line; resource limits abstain instead of silently ignoring unread material.

## Update, restore, remove

Run the new reviewed checkout/archive's installer. It verifies existing managed hashes and rejects local edits, extra files or symlinks. It validates a staging copy before swapping, and keeps the previous installation as a named backup printed in JSON.

```sh
python3 scripts/install.py update --dest "$HOME/.agents/skills/token-router"
python3 scripts/install.py restore --dest "$HOME/.agents/skills/token-router" --backup "/path/printed/as/backup"
python3 scripts/install.py verify --dest "$HOME/.agents/skills/token-router"
python3 scripts/install.py uninstall --dest "$HOME/.agents/skills/token-router"
```

Uninstall only accepts an unmodified managed installation; it does not delete backups, other skills, AGENTS, configuration or authentication. Preserve personal edits separately before updating. For a published-version rollback, use a **clean checkout/archive of the verified previous release** or a validated installation backup—not a single experimental commit revert.

## Cloud and performance

Advanced `--force-model`/legacy latency routing may send candidates+query to OpenAI and consume Codex subscription usage. Default operation never discovers Codex or calls it. Live Luna access is **not validated for this release**; it is not a setup requirement. See the contract before intentionally enabling it. Your main agent may separately send retrieved text to its model.

Measure answer quality, total input+output including skill instructions/selector/recovery, and whole completion time. Existing conditional return experiments do not establish universal savings: the earlier recovery benefit came from selected omitted-return tasks; the target filter saved0.46% on two explicit-target tasks. Those are historical fixed-product observations, not this release's performance. [Release evaluation](docs/release-readiness.md) separates fresh results, offline character counts and unmeasured behavior.

## Development and help

```sh
python3 -m unittest discover -s tests
python3 scripts/run_router_tests.py tests/router-tests.json
```

Both are offline, free of model calls. [CONTRIBUTING.md](CONTRIBUTING.md), [SUPPORT.md](SUPPORT.md), [SECURITY.md](SECURITY.md). MIT [license](LICENSE). Public samples are synthetic; research source downloads are separately pinned and licensed, and excluded from the runtime archive.

## Evaluation and appropriate use

Four fixed installed-skill/ordinary-search pairs both answered4/4 correctly. Skill-enabled total tokens were10.65% higher; every task used ordinary search and no router call. This sample demonstrates avoiding needless routing, not savings or automatic discovery. It does not measure the extractor’s benefit on broad large-log questions. A separate replay of the four historical files preserves the released extractor’s output exactly; historical token savings are not relabeled as new measurements. Separately,24 offline default packets match the public release baseline;20 contain all initial required evidence. Detailed conditions and hashes are in the repository [evaluation](docs/release-evaluation/README.md).

## Development candidate (not part of v2.6.0 release)

This branch experiments with `--search-term TEXT --line-numbers` for bounded literal windows and citation-ready lines. It aims to avoid broad structural extraction for questions with known anchors. Adoption requires new same-task comparisons against ordinary search, including all model/skill/follow-up costs. See references/contract.md.

The dev reader accepts `--search-context 0..12` to request a smaller explicit literal window. Defaults and traceback/source/output safety checks stay unchanged. This option does not establish total-token savings; the revised discovery scope targets dispersed evidence rather than single-location searches.

The dual-brain review and new same-task measurements are in [docs/token-value-review/report.ko.md](docs/token-value-review/report.ko.md). Completed comparisons show conditional savings; one unknown-usage timeout and the attrs cost increase prevent a universal savings claim or stable promotion.

The unreleased2.7.0 automatic log-only gate and streamed timeout accounting were rechecked in [activation-gate review](docs/activation-gate-review/report.ko.md). Excluded tasks had no observed skill/reader invocation, but the complete pilot used25.9% more tokens. Release/global promotion is blocked; stable2.6.0 remains recommended. No general token savings claim is made.
