# Contributing

Default routing is Python-only and must not discover or call a model. Keep original decoded text, line coordinates and shared safety checks. Return completion and exact target filtering are optional; do not conflate them with policy-version.

```sh
python3 -m unittest discover -s tests
python3 scripts/run_router_tests.py tests/router-tests.json
python3 scripts/build_release.py --output dist
python3 scripts/smoke_archive.py dist/token-router-2.7.0-dev.zip
```

Build from a clean committed source. Offline CI needs no model/login/secret; checkout and Python setup still use infrastructure network. Live comparisons require a separate explicit budget and sanitized licensed sources. Keep raw research evidence immutable and out of runtime archives; publish sanitized summaries and pinned replay instructions. Record product commit/module hashes, policy, model and source/prompt hashes. Failed/unknown usage is not zero.

Use small reviewable commits and behavioral tests for source/cap/option/installation failures. Do not add providers, agents, daemons or persistent indexes as incidental fixes. Report test platforms actually executed, not just matrix entries. Legacy experiments remain historical and do not establish universal savings.
