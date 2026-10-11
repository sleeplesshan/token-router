## Summary

What changed and why?

## Area

- [ ] `error_log`
- [ ] `heavy_code`
- [ ] `agent_context`
- [ ] Codex CLI compatibility
- [ ] Documentation
- [ ] Tests
- [ ] Community / repository health

## Validation

- [ ] `python3 -m py_compile scripts/router.py scripts/run_router_tests.py`
- [ ] `python3 scripts/run_router_tests.py tests/router-tests.json`
- [ ] Skill validation, if metadata changed
- [ ] Intentional cloud smoke test with sanitized input, if needed (consumes Codex usage)

## Safety

- [ ] I did not add secrets, credentials, private logs, personal data, customer data, or proprietary code.
- [ ] New fixtures are synthetic or sanitized.
- [ ] Documentation warns users not to paste sensitive data into public issues.
