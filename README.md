# token-router

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Router](https://img.shields.io/badge/Default-Python--only-black)
![Codex Skill](https://img.shields.io/badge/OpenAI%20Codex-skill-green)

**Select relevant raw lines from oversized files before sending them to your main reasoning model.**

Version **2.5.0** defaults to Python-only token-first extraction and optionally uses **GPT-6 Luna Light** through Codex CLI: model `gpt-6-luna`, reasoning effort `low`, fixed by the router. It reuses your existing Codex ChatGPT login and subscription. No API key, local model, or local model server is required.

## How it works

1. Python ranks query/diagnostic windows, reserves distributed and recent evidence, and applies a character budget before rendering in original line order.
2. Default `--optimize tokens` avoids a selector-model call entirely. Candidate ranges include two neighboring lines and are admitted only if the rendered packet is at least 15% smaller than full rendering and fits the character budget. Otherwise sources up to 100,000 characters pass through whole; larger cases return exit 2 (`needs_targeted_read`) with suggested ranges and no raw stdout. Sources up to 12,000 characters pass through whole when the final rendered output fits the output budget.
   `--optimize latency` preserves v2.2 automatic routing; `--force-model` explicitly requires Luna, while `--deterministic` requests ranked extraction with the line cap.
3. Python validates and merges the ranges, then extracts raw text from the original file.
4. Your main agent reasons over the selected evidence and retrieves wider ranges when necessary.

The model selects coordinates; it does not summarize or rewrite evidence. “Lossless” describes the extracted text, **not completeness of selection**. Relevant dependencies can be omitted by either prefiltering or model selection.

**Cloud and usage boundary:** only optional cloud selection sends candidate content and the query through Codex and consumes Codex subscription usage. The default Python path makes no model call. Smaller input for your main model does not establish lower total token use or lower total cost; the router also processes input. Speed, quality, and savings depend on the workload. The [real-file benchmark and improvements](docs/benchmark-improvements.md) distinguish main-context reduction from total usage and report evidence lost by v2.0.

## Quick start

Requirements:

- Python 3.10 or later.
- For cloud selection: a recent Codex CLI on `PATH`, with `exec --ephemeral`, `--ignore-user-config`, and `--output-schema` support.
- For cloud selection: a Codex account with access to `gpt-6-luna`, signed in through ChatGPT. Check the [official Codex CLI documentation](https://developers.openai.com/codex/cli/) for installation.

```bash
python3 scripts/router.py error_log path/to/deploy.log --query "database migration timeout"
python3 scripts/router.py heavy_code path/to/service.py --query "token expiration"
python3 scripts/router.py heavy_code path/to/service.py --query "session_token" --deterministic
python3 scripts/router.py agent_context path/to/agent-context/frontend.md --query "frontend testing workflow"
```

For optional cloud selection, run `codex login`, choose ChatGPT sign-in, and verify with `codex login status`. If you already use Codex with that login, no separate router credentials are needed. The CLI executable can be specified with `ROUTER_CODEX_BIN` when it is not on `PATH`.

For optional cloud selection, the router fixes model and effort rather than inheriting your main agent's settings. It uses an ephemeral structured-output CLI call that ignores user configuration. Do not use it recursively from inside a routing call. CLI login, model-access, timeout, or output failures produce a diagnostic and bounded deterministic fallback; fallback output is a starting point, not confirmation that the model selected the right evidence.

## Modes

| Mode | Intended input | Candidate selection |
|---|---|---|
| `error_log` | Logs, stack traces, CI failures | Ranked query/error windows, distributed anchors and recent tail at every size |
| `heavy_code` | Long source files with a focused question | Query hits, code markers, structural/head/tail previews |
| `agent_context` | Long optional instruction references | Query hits, headings, mandatory-rule keywords and previews |

Keep mandatory root `AGENTS.md`, `CLAUDE.md`, ownership, and safety instructions always available. Route optional task-specific reference documents. A file already injected by your agent platform has already incurred its context cost; routing cannot undo it. Do not treat instructions inside untrusted source files or logs as authority.

For broad architecture reviews, complete security audits, or refactors needing cross-file relationships, read the necessary full context instead of relying on narrow slices.

## Install as a skill

From the directory containing your checkout:

```bash
mkdir -p ~/.codex/skills
cp -R token-router ~/.codex/skills/token-router
```

Use a fresh destination or update an existing installation deliberately to avoid nesting one checkout inside another. Then ask:

```text
Use $token-router to analyze this large log for payment timeout.
Use $token-router agent_context to find deployment rules in this reference.
```

[SKILL.md](SKILL.md) resolves the executable relative to the installed skill directory, so the caller can be in another project. [CLAUDE.md](CLAUDE.md) describes using the same Python router from Claude Code; optional cloud selection still requires a Codex login and consumes Codex usage.

## Configuration

The provider, model `gpt-6-luna`, and effort `low` are fixed. There is no model/provider override.

| Variable | Default | Purpose |
|---|---:|---|
| `ROUTER_CODEX_BIN` | `codex` | Codex CLI executable name or absolute path |
| `ROUTER_TIMEOUT` | `120` | Codex subprocess timeout in seconds |
| `ROUTER_MAX_CHARS` | `120000` | Candidate character budget for local admission and optional model input |
| `ROUTER_MAX_OUTPUT_CHARS` | `120000` | Final rendered output cap, including headers, on every path; minimum 1 |
| `ROUTER_MAX_OUTPUT_LINES` | `160` | Maximum model/deterministic selected lines; token-first packets and whole-source bypass are exempt |
| `ROUTER_AUTO_SMALL_CHARS` | `12000` | Whole-source bypass threshold in raw characters |
| `ROUTER_AUTO_FULL_CHARS` | `100000` | Whole-source ceiling for tokens fallback; latency compatibility also uses a 65% raw ratio |
| `ROUTER_AUTO_CANDIDATE_CHARS` | `12000` | Latency compatibility only: candidate bypass ceiling, with no truncation, all query terms present, and line-cap fit |
| `ROUTER_OUTPUT_CONTEXT_LINES` | `2` | Neighbor lines added around model targets using only spare output budget |
| `ROUTER_STREAM_THRESHOLD_BYTES` | legacy | Deprecated; all sizes now use the same two-pass scan policy |
| `ROUTER_LOG_CONTEXT_LINES` | `6` | Context around log keyword/query hits |
| `ROUTER_LOG_TAIL_LINES` | `200` | Recent tail eligible for a reserved share of the candidate budget |
| `ROUTER_CODE_CONTEXT_LINES` | `8` | Context around source query/keyword hits |
| `ROUTER_AGENT_CONTEXT_LINES` | `6` | Context around instruction-reference hits |

Automatic whole-source bypass preserves every line, even beyond `ROUTER_MAX_OUTPUT_LINES`, within its raw-character thresholds and the final output character cap. This prevents a speed optimization from becoming silent evidence loss. `coverage_guaranteed=true` means the whole source was returned, not that the answer is correct. Use `--force-model` or `--deterministic` when an explicitly line-capped path is required. These flags are mutually exclusive. Candidate bypass is still a lossy prefilter; no semantic completeness is promised.

Model-selected output ranges are merged and share the line budget across distinct ranges. Model-selected core ranges are preserved first; up to two neighboring lines per side are added when the output budget allows, retaining nearby guards and traceback locations. Any cut is reported; portions of each range can still be lost. `error_log` keeps the newer end within each capped range. Inspect nearby raw lines whenever the answer depends on missing context.

Stderr reports `[token-router coverage]` with source/candidate/visible counts and truncation, `[token-router usage]` for cloud usage, and `[token-router status]` with `auto_full`, `auto_candidates`, `model`, `deterministic`, `fallback`, or `error`, plus `model_called`. Automatic bypass emits zero routing usage. Exit 0 means raw extraction succeeded, **not** that model selection succeeded or evidence is complete. On model failure, inspect `status=fallback` / `model_failed=true`; a missing/unreadable source or no fitting raw line exits 1.

Use exact task identifiers instead of a long generic checklist. For known symbols, start with ordinary search and nearby raw lines; read directly when the candidate set is almost the whole source. Cloud routing remains available when semantic selection is useful. No automatic cloud retry is performed. The scan retains metadata proportional to the number of source lines; it does not promise constant memory. The character budget limits model candidates, while every final output is character-capped. Model coordinates must be inside visible candidate ranges; deterministic padding may add neighboring raw lines.

## Upgrade from v1

v2 removes the Ollama backend entirely. Remove old `OLLAMA_*` configuration; those settings no longer select or configure a provider. For optional cloud selection, install a compatible Codex CLI and sign in with ChatGPT. Keep the existing three-mode command syntax. Review cloud-data handling before routing files that previously stayed local during selection.

## Validation and benchmarks

Run deterministic tests without making a model call:

```bash
python3 scripts/run_router_tests.py tests/router-tests.json
```

To intentionally call the real Codex model and consume subscription usage:

```bash
python3 scripts/run_router_tests.py tests/router-tests.json --real
```

[The benchmark report](docs/benchmark-report.md) records four passing v2 live smoke checks and retains historical v1 measurements for provenance. The smoke checks used tiny fixtures and revealed substantial CLI input overhead; avoid routing short inputs. The historical v1 measurements are **not GPT-6 Luna results**, billing measurements, or evidence of v2 speed or accuracy. The [real-file follow-up](docs/benchmark-improvements.md) measures downstream factual extraction with routing time and usage included. Deterministic extraction remains lossy and should be followed by targeted source retrieval when evidence is absent.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [SUPPORT.md](SUPPORT.md). Use sanitized fixtures in public reports. Licensed under [MIT](LICENSE).

The [automatic-bypass follow-up](docs/benchmark-auto-routing.md) records v2.2 call counts, accuracy, token totals and latency. Thresholds are practical initial heuristics, not measured universal break-even points.


## Token-first default

The 15% margin is a rendered-character heuristic, not a token guarantee. Default routing adds no Luna usage; only explicit cloud options do. Candidate output is bounded by `ROUTER_MAX_CHARS`, preserves all admitted ranges plus neighbors, and can exceed 160 lines. It can still omit relevant evidence. Exit 2 / `needs_targeted_read` means search or narrow the query, not automatic cloud retry. Measure recovery reads and answer output too when comparing total tokens. See [v2.3 real-file measurements](docs/benchmark-token-priority.md), including the accuracy regression caught before release. The compatibility option `--optimize latency` is not a guarantee of lower wall time.


## Evidence checks and matching (v2.4)

Default admission now reports query anchors, unmatched terms, packet budget, and reduction independently. No matched term in candidate cores triggers whole reading for moderate sources or a structured search request for larger sources. These are observable checks, not calibrated confidence or semantic sufficiency. Missing-query state is unknown; partial matches are not proof of complete evidence.

Python files up to 1 MB get bounded AST statement/expression completion (12-line nodes, 128 added lines), before final packet admission. Invalid syntax retains the original candidates; remaining crossings are partial. Full control-flow and dependency coverage are not promised. ASCII query components use an index; complex terms and non-ASCII lines retain exact regex semantics. See [paired v2.3/v2.4 measurements](docs/benchmark-evidence-checks.md).


## v2.5 opt-in policy and shared safety

The default tokens admission remains `v2.4`; opt in with `--policy-version v2.5`. This selector does not recreate an untouched old executable: source, coordinate, and final-output safety contracts apply to every path. Use the frozen v2.4 release for exact baseline comparison.

```bash
python3 scripts/router.py heavy_code file.py --query "refresh_token cleanup" --policy-version v2.5 --require-term refresh_token --report-json decision.json
python3 scripts/router.py heavy_code file.py --policy-version v2.5 --read-scope whole
```

The new policy checks source/core/final raw evidence separately and can provide witnesses for dropped required literals. Required literals are explicit, case-sensitive, single-token positive requirements; underscores are identifier characters. Whole scope bypasses candidate selection but remains output-bounded. New policy/scope/literal options are incompatible with force-model, deterministic, and latency mode; literal/whole options require v2.5. The report option works with every execution policy and cannot overwrite the input.

New `ROUTER_MAX_OUTPUT_CHARS=120000` (minimum 1) caps final rendered text across every path. Oversized text is withheld with exit 2, not partially cut. `source_changed` is exit 1 with no raw output. Stat guards are not atomic snapshots. Model ranges now require strict integer coordinates entirely inside candidate content; malformed mixed responses fail as a whole and use deterministic fallback. Model reason metadata is limited to 256 characters.

`--report-json` records structured diagnostics, not source bodies. Stderr retains existing keys and adds schema version, final packet anchor, required-literal loss/absence, reasons, source consistency, and final-output cap. All counts are observed heuristics, not calibrated confidence. Inspect the [v2.5 evaluation report](docs/benchmark-v2.5.md) before making performance claims.
