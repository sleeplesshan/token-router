# CLI and data contract — 2.7.1

Runtime: Python 3.10–3.14, standard library. Default: `--optimize tokens`, policy v2.4, return-context off. No executable discovery, login, network or telemetry occurs in this default. Basic regular-file CLI is designed for Linux/macOS/Windows; see the release-readiness report for actually executed platforms. Research scripts have separate dependencies and are not installed.

## Combinations

| Option | Local tokens | deterministic / force-model / latency |
|---|---|---|
| query, report-json, line-numbers, compact-status | Supported | Supported |
| search-term / search-context | focused only; context requires literal terms | Usage error |
| activation-profile log-context | error_log + search-term only; bypass exit2 | Usage error |
| symbol QUALNAME | heavy_code + focused only; incompatible with search terms/required literals/return completion | Usage error |
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
- 2 + `status=bypass`: optional profile rejected; empty raw stdout, ordinary targeted search.
- 2 + `status=usage_error`: invalid command, printed in structured stderr after argparse text. No sidecar is created for invalid arguments.
- 130: interrupted cloud operation, no raw stdout.

Stderr retains `[token-router status]` and earlier coverage/decision/usage keys. `--report-json PATH` atomically replaces a diagnostic file only after validation; it cannot alias the source. On report write failure, raw output is withheld. A source change removes the designated stale report, including a previous success report; inability to remove it is explicitly reported. A pre-existing report can remain on other earlier failures: only trust a sidecar from a successful current invocation and check exit/stderr. A final source-error report has status error, not stale success. Windows uses native FILE_BASIC_INFO ChangeTime because its stat ctime is creation time; unsupported metadata queries fail closed. Windows may prevent deleting or rotating an open descriptor, while replacement between reads is still checked. Metadata guards detect normal mutation/replacement/rotation; they do not create an atomic snapshot. A same-size write whose modification time is restored and change timestamp remains in the same filesystem/clock tick can be missed. Use an immutable source copy when strict snapshot consistency is required.

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

## Explicit search and numbered presentation — 2.7.0

Version2.7.0 adds repeated `--search-term TEXT`: case-sensitive substring search with12 neighboring lines for code/references and4 for logs around every match, merged across overlaps. It bypasses structural ranking/AST/tail. Selected log windows overlapping a recognizable Python traceback extend to its terminating exception only within64 lines; timestamp/ANSI parsing identifies bounds without changing raw text. Log literals match raw text or its ANSI-SGR-stripped view, so colored ERROR markers remain searchable. Case is preserved. Unselected blocks are excluded. Search terms are explicit selection hints, not required-literal evidence. It supports focused local tokens only; cloud/deterministic/whole/required literals/return completion combinations are usage errors. Missing terms are reported, not guessed. Complete windows exceeding12,000rendered characters or the common final cap are withheld; narrow the search. Non-small sources still require at least15% reduction. No terms are inferred from gold or natural-language prose.

`--line-numbers` is presentation-only across paths: original decoded text and coordinates remain unchanged in Packet.raw_slices; stdout uses NUMBERED CONTENT headers and prefixes each original line. The final cap includes prefixes and headers. Default raw output remains compatible. Coordinates make citation-only re-reading unnecessary. Shared source/coordinate/input/output/sidecar checks still apply.

Managed updates under .agents/skills or .codex/skills put backups under the sibling skill-backups directory, outside discovery. This prevents old instructions being exposed as another current skill. Existing backups are preserved; move historical sibling backup directories out of the discovery root explicitly.

`--search-context N` (0-12) overrides neighbors only for `--search-term`; other paths reject it. Omitted values preserve code12/log4. Width0 retains every matching line, not ordinary neighbors; selected bounded tracebacks can still add lines. An ERROR before an unselected traceback does not select it at width0. This is explicit scope control, not a claim of semantic completeness. Use wider context for branch conditions or multiline expressions and include recovery costs in comparisons.

Discovery is scoped to dispersed error-log context or branching/order audits requiring complete Python definitions whose exact qualified names are already known. Literal-only lookups, one already-known line range and sufficient visible evidence should bypass loading. This metadata guideline is not a programmable host interception or a future total-token guarantee. The prior log-only gate failed promotion. The explicit native complete-callable/failure-block evaluation is in docs/actual-reader-review/report.ko.md; cold implicit savings remain unproven.

## Explicit complete Python callables — 2.7.0

For an explicit request needing complete known callables, batch qualified names:

```sh
python3 "<skill>/scripts/router.py" heavy_code "<file>" --symbol "Class.method" --symbol "helper" --line-numbers --compact-status
```

Repeated `--symbol QUALNAME` selects1-8 exact qualified functions/async functions, including decorators. It requires focused local heavy_code tokens; it cannot combine with literal windows, required terms, return completion, deterministic, latency or cloud. The guarded probe is capped at1,000,000 decoded characters; line resource bounds still apply. Duplicate definitions (including overloads/property pairs), absent names and invalid Python withhold the whole batch. Overlapping definitions merge, preserving original lines without duplication. Full rendered batch must fit12,000 and the common output cap and retain the existing reduction margin. Complete definitions are not complete dependencies or enclosing conditional context.

Selected bounded pytest failure blocks may extend from a recognized underscore header to their file:line:exception terminator within64 lines. Unselected blocks remain excluded. `--compact-status` changes only stderr presentation; current errors/actions/model flags remain and `--report-json` retains the full report. Raw/numbered stdout and the shared safety validation remain identical.

Compact successful symbol output omits coordinates already present in stdout; failure symbol ranges and suggested ranges remain bounded. `symbol_occurrences` and `symbol_ranges_truncated` describe repeated definition positions, not answer probability. Named/literal selection does not use general query ranking; the query policy version has no new semantic sufficiency role there. Model reason/output/source validation is unchanged.

## Conservative host activation — 2.7.1

`routing_policy.plan_activation` is an I/O-free host API for pre-guide eligibility: native guide delivery, failure-context log purpose,2–32 known selectors with at least two distinct literals, and insufficient visible evidence. Unknown purpose, code, simple lookup, visible evidence and cold delivery bypass. It does not classify prose, inspect source or predict billed savings. Installation alone cannot attach middleware; the host owning the main turn must connect it.

`--activation-profile log-context` is additive and optional, only error_log with local literal search. Existing scan facts require source50,000 decoded chars, separate selected regions2+/span100lines+, a selected recognized complete failure block1+, all terms found and selected line cost at most half the bounding region. Existing rendered caps and general15% margin are unchanged. Rejects return no source; no whole/cloud fallback. Source/sidecar errors override activation. `activation`, `activation_profile`, sidecar-only `activation_facts` are observations; require exit0 and successful status before consuming evidence. Compact stderr omits scan details. Manual commands without the profile and query policy remain unchanged.

Native regression showed lower log tokens with slower completion, not universal or implicit savings. [Integration](https://github.com/sleeplesshan/token-router/blob/v2.7.1/docs/activation-integration.md) and [evaluation](https://github.com/sleeplesshan/token-router/blob/v2.7.1/docs/conservative-activation-review/report.ko.md).
