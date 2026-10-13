# Sources and provenance

Public upstream materials, reused as development/regression sources. Two repetitions are not independent projects. Downloads/preparation precede model episodes. Runtime release archives contain no upstream source bodies or benchmark events.

| Local source | Upstream | Bytes | SHA-256 |
|---|---|---:|---|
| pandas_frame.py | [Pinned source](https://github.com/pandas-dev/pandas/blob/0691c5cf90477d3503834d983f69350f250a6ff7/pandas/core/frame.py) | 447,104 | `9b813159606b62af03bfe76a7089da282d2d6091f308cf2f4d90dd0661a01105` |
| rich_console.py | [Pinned source](https://github.com/Textualize/rich/blob/9d8f9a372cc5916fd4781fec207ced7ddac2f08f/rich/console.py) | 101,361 | `4533fc66963623a2a21447b501d6f51f8cfee7e14775178093a5e6eb61dc135a` |
| cpython-ubsan.log | [Pinned source](https://github.com/python/cpython/actions/runs/38139579572/job/114470618995) | 551,037 | `d23199487e0009822f4d3a33284fb9a42da018155164c308e96cad456611d606` |
| scipy-fast.log | [Pinned source](https://github.com/scipy/scipy/actions/runs/38118134919/job/114407140306) | 638,795 | `23cc02f4ecff02141897d670bf831f5be62702b33c2a48e6e5c2b717fd783ca3` |

Upstream notices are retained under [prior third-party notices](../actual-reader-review/third-party/): pandas BSD, Rich MIT, Python PSF, SciPy BSD. Source excerpts in research traces retain those upstream terms; the project MIT license does not relicense third-party material. SciPy notice was retrieved2026-10-13 from upstream main; log provenance is its immutable job URL and content SHA, not that notice snapshot.


SymPy source: [immutable CI job](https://github.com/sympy/sympy/actions/runs/38330342967/job/115078685188),commit4120faf4bfe6aaa81675718fc5566833ff9f1999.917lines,84004bytes,SHA256add4fe82b292e7188fbf58eb6589f801565886b729c3d36f7299dc40c63d1800. [BSD notice](SYMPY-LICENSE). The original full log is unchanged. All four actual files are under sources/. New CI family at first collection; final analysis treats it as development/regression.

Codex0.162.1 primary contracts: [namespace instructions](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/codex-mcp/src/rmcp_client.rs#L840),[exposure policy](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/core/src/tools/spec_plan.rs#L199),[local startup cwd](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/rmcp-client/src/stdio_server_launcher.rs#L277),[MCP stdio](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports). Full main network request body and physical transport retries are not exposed; main-turn count is not HTTP-request count.
