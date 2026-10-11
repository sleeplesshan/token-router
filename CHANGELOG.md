# Changelog

## 2.2.0 — 2026-10-12

- Skip unnecessary Luna calls automatically for small whole sources, dense candidates in moderate sources, and small untruncated query-matching candidates.
- Preserve the entire source on full bypass instead of silently applying the selection line cap.
- Add `--force-model` to retain explicit cloud selection; keep `--deterministic` as explicit bounded local extraction.
- Report `model_called`, distinct bypass statuses, raw candidate character counts and zero routing tokens when no model runs.
- Add threshold, evidence-preservation and override regressions; record actual-file follow-up in [the report](docs/benchmark-auto-routing.md).

## 2.1.0 — 2026-10-12

- Rank candidates before applying the character cap; preserve distributed anchors and a tail share at every file size.
- Remove generic question words, match Unicode/symbol boundaries, and downweight repeated diagnostics.
- Preserve bounded context for the first named pytest failure block.
- Share output budgets across distinct ranges and add nearby lines without displacing selected core evidence.
- Add `--deterministic` to retrieve raw evidence without any model call.
- Return ranked raw fallback on model failure at all file sizes, with explicit status and coverage diagnostics. Exit 0 indicates usable extraction, including fallback; inspect `model_failed`.
- Replace the skill's line-count trigger with search-first and evidence-completeness guidance. Keep GPT-6 Luna Light and ChatGPT subscription authentication fixed.
- Add regressions for noisy queries, Unicode identifiers, repeated errors, distributed evidence, fallback, and context padding. See [real-file validation](docs/benchmark-improvements.md).

## 2.0.0 — 2026-10-11

### Breaking changes

- Replace the local Ollama backend completely with Codex CLI using fixed GPT-6 Luna (`gpt-6-luna`) and Light (`low`) reasoning.
- Require an existing Codex ChatGPT login and model access. Real calls send candidate content to the cloud and consume subscription usage; no separate API key is used.
- Remove all `OLLAMA_*` settings and local-model dependencies. The three existing routing modes and command syntax remain available.

### Changes

- Use an ephemeral, read-only CLI run with a compact routing instruction file, JSON output schema, stdin prompts, and bounded timeout.
- Ignore user model configuration for the child invocation, disable shell/multi-agent/apps/web/hooks/memory features, and guard against recursive routing.
- Preserve deterministic prefiltering, raw text extraction, output caps, and bounded fallback behavior.
- Match Unicode query terms, including Korean.
- Print the CLI-reported routing token usage to stderr without mixing it into raw slices.
- Add transport regression tests and an offline GitHub Actions test matrix.
- Update the global skill instructions and clearly separate historical benchmarks from v2 smoke checks.

### Validation

Ten fixture regression cases, ten transport/unit tests, and four live Codex selection checks passed. Live checks cover all three modes. These small fixtures do not establish general accuracy, speed superiority, or net usage savings. See [the report](docs/benchmark-report.md).
