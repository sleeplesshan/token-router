# Changelog

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
