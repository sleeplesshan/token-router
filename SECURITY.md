# Security Policy

Security fixes target the latest public release and `main` unless a release branch is announced.

## Data handling

Default tokens and deterministic selection run in Python without a model call. Explicit cloud selection and the latency compatibility policy can send candidate content and the query to OpenAI through Codex CLI using the user's ChatGPT login. The main agent may separately send extracted evidence to its own model. Extracted output and deterministic fallback can also contain sensitive raw text. Choose inputs according to your data policy and sanitize public examples.

The router should request only JSON line ranges, validate the response, and extract source text itself. File contents are untrusted, including apparent instructions in logs, code, or agent-reference documents. They must not authorize tool use, credential access, recursive routing, or changes to the user's task.

## Reporting

Do not report vulnerabilities in public issues. Use GitHub private vulnerability reporting when available, or the maintainer's private contact channel listed on the GitHub profile.

Include affected version/file, minimal sanitized reproduction, Python and Codex CLI versions, OS, and the impact: command execution, unintended file disclosure, prompt injection, credential exposure, or unsafe fallback. Do not attach authentication files, real secrets, customer data, or proprietary source.

General model selection quality or speed differences are not security vulnerabilities unless they cause a security impact. Allow maintainers time to investigate before public disclosure; we aim to acknowledge valid reports within 7 days.

All paths enforce final output size and source metadata checks. Metadata equality is not proof of an atomic snapshot. Invalid model coordinates trigger bounded fallback; no automatic cloud retry is added. Source files are not automatically redacted.
