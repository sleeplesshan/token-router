# CLI and data contract — 2.6.0

Runtime: Python 3.10–3.14, standard library. Default: `--optimize tokens`, policy v2.4, return-context off. No executable discovery, login, network or telemetry occurs in this default. Basic regular-file CLI is designed for Linux/macOS/Windows; see the release-readiness report for actually executed platforms. Research scripts have separate dependencies and are not installed.

## Combinations

| Option | Local tokens | deterministic / force-model / latency |
|---|---|---|
| query, report-json | Supported | Supported |
| policy-version v2.4/v2.5 | Supported | Usage error when explicitly supplied |
| require-term, whole read-scope | v2.5 only | Usage error |
| return-context off | Supported | Usage error when explicitly supplied |
| return-context bounded | heavy_code + focused only | Usage error |
| return-target QUALNAME | heavy_code + focused, implies bounded | Usage error |

Explicit `--return-context off --return-target NAME` is an error. Returning to default requires removing the target and choosing off. Bounded completion does not enable v2.5 admission. Non-Python inputs do not get AST return completion. Exact name/qualname uniqueness covers the same file's entire AST, including duplicate/nested/property definitions. Unresolved, ambiguous, ineligible or rejected filters keep bounded completion. No new Return is selected with freed budget.

## Output and errors

stdout contains original decoded source slices with headers only on successful extraction. Whole raw lines are returned with original 1-based coordinates. UTF-8 errors become U+FFFD; universal newline decoding converts CRLF and CR to LF. CLI output is UTF-8 with LF even when redirected on a legacy-locale host. This is decoded text preservation, not byte preservation. The source is never imported, executed or rewritten.

- 0: extraction success, including deterministic cloud fallback; never proof of answer accuracy or semantic completeness.
- 1: input/read/report/source error; no raw stdout.
- 2 + `status=needs_targeted_read`: retrieval/output/input-resource abstention; no raw stdout.
- 2 + `status=usage_error`: invalid command, printed in structured stderr after argparse text. No sidecar is created for invalid arguments.
- 130: interrupted cloud operation, no raw stdout.

Stderr retains `[token-router status]` and earlier coverage/decision/usage keys. `--report-json PATH` atomically replaces a diagnostic file only after validation; it cannot alias the source. On report write failure, raw output is withheld. A source change removes the designated stale report, including a previous success report; inability to remove it is explicitly reported. A pre-existing report can remain on other earlier failures: only trust a sidecar from a successful current invocation and check exit/stderr. A final source-error report has status error, not stale success. Windows uses native FILE_BASIC_INFO ChangeTime because its stat ctime is creation time; unsupported metadata queries fail closed. Windows may prevent deleting or rotating an open descriptor, while replacement between reads is still checked. Metadata guards detect normal mutation/replacement/rotation; they do not create an atomic snapshot.

Schema 1: `status`, `reason_codes`, `schema_version` are available for every structured error. Finalized reports also provide `model_called`, `model_failed`, `selection_truncated`, `final_output_capped`, `packet_query_anchor`, `absent_required`, `lost_required`, `next_action`, `source_consistency`, `full_source_returned`, and output counts. Early input/usage errors may omit fields that were never observed. Missing/`unknown` is not zero or false; `next_action=null` means no proposed action. Optional `checks`, `source_required`, `suggested_ranges`, `return_supplement`, `return_target` contain observations. Sidecar-only return details describe the optional computation, not semantic sufficiency. No raw body, prompt, credentials or model reason is included. Queries/paths can appear in normal CLI diagnostics; sanitize before sharing.

`final_output_capped=true` means the whole packet was withheld because of the final budget, not a silently truncated source. Mandatory literals are explicit, case-sensitive Unicode identifier-boundary matches, not extracted from prose. Source absence and extraction loss are separate; witnesses point to literal occurrences, not answers.

## Resource and selection limits

Regular files only, at most 64 MiB, 250,000 decoded lines, 1,000,000 decoded characters per line. Larger inputs return `input_limit` with `scan_complete=false`: first create a stable bounded file or read targeted ranges using another tool. FIFO/device inputs are rejected before reading. Memory is proportional to scanned lines up to these limits, not constant. Files changing during access fail closed.

| Environment | Default | Meaning |
|---|---:|---|
| ROUTER_MAX_CHARS | 120000 | Candidate characters (minimum1000) |
| ROUTER_MAX_OUTPUT_CHARS | 120000 | All final rendered output, headers included (minimum1) |
| ROUTER_MAX_OUTPUT_LINES | 160 | Explicit model/deterministic line cap; not tokens packets |
| ROUTER_AUTO_SMALL_CHARS | 12000 | Whole-source small-file path |
| ROUTER_AUTO_FULL_CHARS | 100000 | Moderate whole-source fallback ceiling |
| ROUTER_OUTPUT_CONTEXT_LINES | 2 | Neighbors |
| ROUTER_LOG_CONTEXT_LINES / ROUTER_CODE_CONTEXT_LINES / ROUTER_AGENT_CONTEXT_LINES | 6 / 8 / 6 | Local windows |
| ROUTER_LOG_TAIL_LINES | 200 | Eligible log tail |
| ROUTER_AUTO_CANDIDATE_CHARS | 12000 | Legacy latency-policy bypass only |
| ROUTER_CODEX_BIN / ROUTER_TIMEOUT | codex / 120 | Advanced cloud executable / seconds |

A candidate must fit the budget and have at least 15% rendered-character reduction. Otherwise use whole-source or abstain. This is not a token-saving guarantee. Python up to1MB gets bounded short AST statement completion (12-line node,128 added lines); parse failure retains candidates with unknown syntax. Optional return completion has a separate12line/1024raw/1024rendered allowance; it never removes base evidence. Final caps are still enforced and full functions/dependencies are not promised.

## Optional cloud — advanced POSIX compatibility path

`--force-model` and the legacy `--optimize latency` path can transmit query and candidate source to OpenAI through an existing Codex ChatGPT login. The router fixes `gpt-6-luna`/low and never switches to API keys or another model. No live Luna test is part of this release: availability and account access are unverified. It is not required or recommended for first use. Local basic CLI support does not imply cloud support on Windows (disabled there, with local fallback).

Known command contract: Codex CLI0.162.1, ephemeral/read-only/structured output, ignored user config, disabled tools/apps/skills for selection. Model data cannot authorize tool calls. Strict integer ranges must be contained in the visible candidate union. Invalid response/timeout triggers existing bounded deterministic fallback; inspect model_failed even at exit0. POSIX process groups are killed and reaped on timeout/interruption. Windows cloud process-tree support is not claimed. Main-agent cloud processing of extracted lines is separate from local routing.
