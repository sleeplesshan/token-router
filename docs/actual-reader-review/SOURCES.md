# Sources and provenance

Public upstream materials, reused as development/regression sources. Two repetitions are not independent projects. Downloads/preparation precede model episodes. Runtime release archives contain no upstream source bodies or benchmark events.

| Local source | Upstream | Bytes | SHA-256 |
|---|---|---:|---|
| pandas_frame.py | [Pinned source](https://github.com/pandas-dev/pandas/blob/0691c5cf90477d3503834d983f69350f250a6ff7/pandas/core/frame.py) | 447,104 | `9b813159606b62af03bfe76a7089da282d2d6091f308cf2f4d90dd0661a01105` |
| rich_console.py | [Pinned source](https://github.com/Textualize/rich/blob/9d8f9a372cc5916fd4781fec207ced7ddac2f08f/rich/console.py) | 101,361 | `4533fc66963623a2a21447b501d6f51f8cfee7e14775178093a5e6eb61dc135a` |
| cpython-ubsan.log | [Pinned source](https://github.com/python/cpython/actions/runs/38139579572/job/114470618995) | 551,037 | `d23199487e0009822f4d3a33284fb9a42da018155164c308e96cad456611d606` |
| scipy-fast.log | [Pinned source](https://github.com/scipy/scipy/actions/runs/38118134919/job/114407140306) | 638,795 | `23cc02f4ecff02141897d670bf831f5be62702b33c2a48e6e5c2b717fd783ca3` |

Upstream notices are retained under [third-party/](third-party/): pandas BSD, Rich MIT, Python PSF, SciPy BSD. Source excerpts in research traces retain those upstream terms; the project MIT license does not relicense third-party material. SciPy notice was retrieved2026-10-13 from upstream main; log provenance is its immutable job URL and content SHA, not that notice snapshot.

Native protocol schemas were generated locally from Codex0.162.1 using `codex app-server generate-json-schema --out DIR`. The reviewed `TurnStartParams.UserInput` includes `skill` with `name`/`path`; `ThreadTokenUsageUpdatedNotification` exposes cumulative input/output and cached/reasoning subsets. Native input selected the installed guide by path before execution. Original local protocol/startup and hashes are retained; public event archives begin at turn/started and omit unrelated installed-skill inventory/startup environment. Target skill audit paths use a portable placeholder. Main prompts/instructions/source hashes and installed file inventory are pinned in the execution lock.

Full network request body and internal transport retries are not exposed by the host. Do not equate48 main turns with48 physical model HTTP requests.
