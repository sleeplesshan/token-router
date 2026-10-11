# token-router

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Router](https://img.shields.io/badge/Router-GPT--6%20Luna%20Light-black)
![Codex Skill](https://img.shields.io/badge/OpenAI%20Codex-skill-green)

**Select relevant raw lines from oversized files before sending them to your main reasoning model.**

Version **2.2.0** uses **GPT-6 Luna Light** through Codex CLI: model `gpt-6-luna`, reasoning effort `low`, fixed by the router. It reuses your existing Codex ChatGPT login and subscription. No API key, local model, or local model server is required.

## How it works

1. Python ranks query/diagnostic windows, reserves distributed and recent evidence, and applies a character budget before rendering in original line order.
2. An automatic policy skips Luna for small sources, dense candidate sets in moderate sources, or small untruncated candidates. Otherwise Codex CLI sends candidates and your query to GPT-6 Luna Light. `--force-model` disables bypass; `--deterministic` requires bounded Python-only extraction.
3. Python validates and merges the ranges, then extracts raw text from the original file.
4. Your main agent reasons over the selected evidence and retrieves wider ranges when necessary.

The model selects coordinates; it does not summarize or rewrite evidence. “Lossless” describes the extracted text, **not completeness of selection**. Relevant dependencies can be omitted by either prefiltering or model selection.

**Cloud and usage boundary:** candidate content and the query leave your machine through Codex. Each real routing call consumes Codex subscription usage. Smaller input for your main model does not establish lower total token use or lower total cost; the router also processes input. Speed, quality, and savings depend on the workload. The [real-file benchmark and improvements](docs/benchmark-improvements.md) distinguish main-context reduction from total usage and report evidence lost by v2.0.

## Quick start

Requirements:

- Python 3.10 or later.
- For cloud selection: a recent Codex CLI on `PATH`, with `exec --ephemeral`, `--ignore-user-config`, and `--output-schema` support.
- For cloud selection: a Codex account with access to `gpt-6-luna`, signed in through ChatGPT. Check the [official Codex CLI documentation](https://developers.openai.com/codex/cli/) for installation.

```bash
codex login
codex login status
python3 scripts/router.py error_log path/to/deploy.log --query "database migration timeout"
python3 scripts/router.py heavy_code path/to/service.py --query "token expiration"
python3 scripts/router.py heavy_code path/to/service.py --query "session_token" --deterministic
python3 scripts/router.py agent_context path/to/agent-context/frontend.md --query "frontend testing workflow"
```

Choose ChatGPT sign-in when logging in. If you already use Codex with that login, no separate router credentials are needed. The CLI executable can be specified with `ROUTER_CODEX_BIN` when it is not on `PATH`.

The router fixes model and effort rather than inheriting your main agent's settings. It uses an ephemeral structured-output CLI call that ignores user configuration. Do not use it recursively from inside a routing call. CLI login, model-access, timeout, or output failures produce a diagnostic and bounded deterministic fallback; fallback output is a starting point, not confirmation that the model selected the right evidence.

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

[SKILL.md](SKILL.md) resolves the executable relative to the installed skill directory, so the caller can be in another project. [CLAUDE.md](CLAUDE.md) describes using the same Python router from Claude Code; routing still requires a Codex login and consumes Codex usage.

## Configuration

The provider, model `gpt-6-luna`, and effort `low` are fixed. There is no model/provider override.

| Variable | Default | Purpose |
|---|---:|---|
| `ROUTER_CODEX_BIN` | `codex` | Codex CLI executable name or absolute path |
| `ROUTER_TIMEOUT` | `120` | Codex subprocess timeout in seconds |
| `ROUTER_MAX_CHARS` | `120000` | Maximum line-numbered candidate content sent to the router model |
| `ROUTER_MAX_OUTPUT_LINES` | `160` | Maximum extracted raw lines returned to the main agent |
| `ROUTER_AUTO_SMALL_CHARS` | `12000` | Whole-source bypass threshold in raw characters |
| `ROUTER_AUTO_FULL_CHARS` | `100000` | Whole-source bypass ceiling when candidate raw characters cover at least 65% of source |
| `ROUTER_AUTO_CANDIDATE_CHARS` | `12000` | Candidate bypass ceiling; also requires no truncation, all query terms present, and fit within output line cap |
| `ROUTER_OUTPUT_CONTEXT_LINES` | `2` | Neighbor lines added around model targets using only spare output budget |
| `ROUTER_STREAM_THRESHOLD_BYTES` | legacy | Deprecated; all sizes now use the same two-pass scan policy |
| `ROUTER_LOG_CONTEXT_LINES` | `6` | Context around log keyword/query hits |
| `ROUTER_LOG_TAIL_LINES` | `200` | Recent tail eligible for a reserved share of the candidate budget |
| `ROUTER_CODE_CONTEXT_LINES` | `8` | Context around source query/keyword hits |
| `ROUTER_AGENT_CONTEXT_LINES` | `6` | Context around instruction-reference hits |

Automatic whole-source bypass preserves every line, even beyond `ROUTER_MAX_OUTPUT_LINES`, within its raw-character thresholds. This prevents a speed optimization from becoming silent evidence loss. `coverage_guaranteed=true` means the whole source was returned, not that the answer is correct. Use `--force-model` or `--deterministic` when an explicitly line-capped path is required. These flags are mutually exclusive. Candidate bypass is still a lossy prefilter; no semantic completeness is promised.

Model-selected output ranges are merged and share the line budget across distinct ranges. Model-selected core ranges are preserved first; up to two neighboring lines per side are added when the output budget allows, retaining nearby guards and traceback locations. Any cut is reported; portions of each range can still be lost. `error_log` keeps the newer end within each capped range. Inspect nearby raw lines whenever the answer depends on missing context.

Stderr reports `[token-router coverage]` with source/candidate/visible counts and truncation, `[token-router usage]` for cloud usage, and `[token-router status]` with `auto_full`, `auto_candidates`, `model`, `deterministic`, `fallback`, or `error`, plus `model_called`. Automatic bypass emits zero routing usage. Exit 0 means raw extraction succeeded, **not** that model selection succeeded or evidence is complete. On model failure, inspect `status=fallback` / `model_failed=true`; a missing/unreadable source or no fitting raw line exits 1.

Use exact task identifiers instead of a long generic checklist. For known symbols, start with ordinary search or `--deterministic`; read directly when the candidate set is almost the whole source. Cloud routing remains available when semantic selection is useful. No automatic cloud retry is performed. The scan retains metadata proportional to the number of source lines; it does not promise constant memory. The character budget limits model candidates, while model-selected raw output is limited by lines and can include neighboring or previously omitted source lines.

## Upgrade from v1

v2 removes the Ollama backend entirely. Remove old `OLLAMA_*` configuration; those settings no longer select or configure a provider. Install a compatible Codex CLI, sign in with ChatGPT, and keep the existing three-mode command syntax. Review cloud-data handling before routing files that previously stayed local during selection.

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
