# Contributing to token-router

Preserve the v2 design: Python prefilters input, fixed GPT-6 Luna Light (`gpt-6-luna`, reasoning effort `low`) selects line coordinates through Codex CLI, and Python extracts original text. The model must not summarize or rewrite evidence. The cloud call uses an existing ChatGPT login and consumes Codex subscription usage.

Useful contributions include evidence-recall improvements, deterministic prefilters, bounded fallback behavior, CLI compatibility, and synthetic fixtures for malformed output, non-English content, or omitted dependencies. Keep the provider/model fixed and avoid introducing recursive router calls.

## Validation

```bash
python3 -m py_compile scripts/router.py scripts/run_router_tests.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_router_tests.py tests/router-tests.json
```

Mock tests must not require a login or contact a model. Run `--real` only when intentionally exercising the cloud model with sanitized fixtures. Record Codex CLI version, mode, query, elapsed time, fallback status, and whether the needed evidence was retained. Do not infer live model quality from mock success.

If skill metadata changes, run the skill-creator validator available in your environment:

```bash
python3 /absolute/path/to/skill-creator/scripts/quick_validate.py .
```

Install or expose PyYAML if that validator requires it.

## Pull requests

- Keep scope focused and add tests for meaningful behavior changes.
- Preserve the `error_log`, `heavy_code`, and `agent_context` command forms.
- Document configuration changes and distinguish historical measurements from current results.
- Keep fixtures synthetic or sanitized; never publish credentials, private logs, or proprietary source.
- Evaluate downstream task success and evidence recall alongside output size. Count routing overhead when discussing efficiency.

## Bug reports

Include Python and Codex CLI versions, OS, mode, sanitized command and fixture, relevant `ROUTER_*` settings, and whether the failure concerns authentication/model access, structured output, selection, timeout, fallback, or output caps. State whether `codex login status` confirms ChatGPT authentication; never include credential files or tokens. The model/effort are fixed, so model switching is not a troubleshooting step.
