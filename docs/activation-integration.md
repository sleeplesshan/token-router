# Conservative activation integration

The automatic scope is dispersed failure logs. Complete Python callable retrieval
remains a manual capability: similar code questions had both substantial and
negligible savings. This is task eligibility, not a future-token predictor.

Installing a skill does **not** insert middleware into every Codex read. Metadata
narrows model discovery; a host that owns `turn/start` can enforce the gate before
loading the guide. Without that host integration, pre-loading enforcement is not
available. No global model, auth, hook or AGENTS configuration is changed.

## Host gate before a main turn

Import the installed `scripts/routing_policy.py`. Use facts already available from
the user request or ordinary search; do not read the whole file for this gate.
Do not infer selectors from an answer key. `purpose='failure_context'` means the
task needs block context, not merely a named error or a number from a summary.

```python
from dataclasses import asdict
from routing_policy import plan_activation

decision = plan_activation(
    mode="error_log",
    purpose="failure_context",
    selectors=("ERROR: worker (", "Total test files:"),
    visible_sufficient=False,
    native_guide=True,
)
input_items = [{"type": "text", "text": user_task}]
if decision.action == "activate":
    input_items.append({"type": "skill", "name": "token-router",
                        "path": installed_skill_path})
# Send these items to the existing main turn, using the host's ordinary settings.
# Bypass means the ordinary path: no skill attachment, guide read or router call.
```

This function has no I/O, persistent history, classifier model or additional
model turn. Unknown purpose, fewer than two distinct selectors, sufficient
visible evidence, code tasks or lack of native guide support all bypass.
The host must preserve the declared need and pass known selectors to the agent.
It must never claim a guarantee based on this preliminary decision.

## Extraction gate in the same local command

```sh
python3 scripts/router.py error_log path/to/ci.log \
  --search-term 'ERROR: worker (' --search-term 'Total test files:' \
  --activation-profile log-context --line-numbers --compact-status
```

The existing metadata scan is reused: source at least50,000 decoded characters,
all selectors found, at least two separate selected regions spanning100 lines,
at least one selected recognized complete Python/pytest failure block, and
selected line cost no more than half the bounding region. The whole rendered
packet still has the12,000-character explicit-reader cap and common final cap.
The bounding-region test rejects poor scope; it is **not** a comparison against
efficient batched search and does not change the general15% policy threshold.

Rejection returns exit2, empty raw stdout and a reason. `activation=bypass` with
`next_action=ordinary_search` means use ordinary targeted search; never repeat
the same call or automatically perform whole reading/cloud selection. Runtime
rejection can occur after native guide delivery; that cost must count. An
admitted packet preserves the manual reader's source ranges and raw text.
Source consistency and finalization failures still override output. Detailed
scan facts stay in `--report-json`; compact stderr stays short.

Manual commands without the profile and default query/v2.4 remain unchanged.
The installed21-file inventory is unchanged. The API lives in an existing
runtime module; host integrations are opt-in, not automatically installed.
