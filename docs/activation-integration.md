# Automatic local retrieval — 2.8.1

Recommended Codex installation connects one local read-only tool:

```sh
python3 scripts/install.py install --dest "$HOME/.agents/skills/token-router" --connect-codex
# Existing verified installation:
python3 scripts/install.py connect-codex --dest "$HOME/.agents/skills/token-router"
```

Start a new Codex session after installation, update or connection changes. The
model sees a compact `read_pytest_failures` schema from the start; no skill guide
load or repeated manual invocation is required for everyday retrieval. The setup
skill remains discoverable for setup, diagnostics and explicit manual requests.
Tool selection remains the model's decision, not interception of every read.

## Supported connection and ownership

Codex CLI0.162.1 was tested. The installer uses read-only `codex mcp get` plus config-only app-server RPC.
Creation/deletion replace only `mcp_servers.token-router`; existing matching
connections receive only `omit_tools_from=["deferred"]`. Each scoped write uses
the user config version for compare-and-swap. Version2.8.0 used CLI add/remove,
which can reserialize unrelated MCP entries;2.8.1 removes those mutation calls. It does not start a model/thread, add
another inference provider or alter global models/auth/AGENTS. Direct exposure
has a recurring context cost; deferred discovery did not activate in two pilots.
That observed non-selection is not proof of a universal Codex limitation.

Managed markers record transport and user configuration. Different, disabled,
filtered or subsequently changed settings are preserved and rejected. Installation
can succeed before connection fails: stderr says `installed_connection_failed`
and supplies a reconnect action. CLI-only installation remains usable. A new
registration is removed after failed setup only if its current settings still
match the installer-created record. Concurrent changes are preserved.

Global registration omits cwd. On local Codex0.162.1, the server inherits the
session's local workspace cwd, verified against the official implementation.
It captures that canonical directory as an immutable read root. Home/filesystem
root startup is rejected unless deliberately authorized with explicit roots:

```sh
python3 scripts/install.py connect-codex --dest "$HOME/.agents/skills/token-router" \
  --allow-root /reviewed/project --allow-root /reviewed/logs
```

Changing roots requires disconnect/reconnect. Multiroot/remote environments and
other hosts were not automatically validated. The server does not use dynamic
MCP roots or follow another task's later cwd. New sessions need new server
lifecycles; active processes can retain an earlier release after update.

## Tool and extraction contract

Arguments: local `.log`/`.txt`/`.out` path,2–8 distinct literal failure headers,
optional result fragment (default ` failed`). Known test names are acceptable;
unknown names require ordinary search first. Automatic scope is comparisons of
multiple named pytest blocks and distant results. Single tracebacks, code,
literal answers, one known range and visible sufficient evidence use ordinary
search. There is no project whitelist or future-token predictor.

The stdio MCP server uses Python3.10+ standard library and a fixed, no-shell
local reader subprocess with5second timeout. It rejects outside-root paths and
symlink escapes, scrubs cloud/ROUTER overrides, exposes no cloud/extra CLI flags,
and writes only JSON-RPC on protocol stdout. Requests are limited to65,536bytes;
source/resource and12,000 rendered-character packet caps remain. Failures return
short structured diagnostics without raw source. Calls are synchronous;
cancellation is not processed during the bounded local call. No automatic retry,
recovery engine, network endpoint, source execution or persistent index exists.

The reader reuses `--activation-profile log-context`: source50,000+ decoded
characters, every selector present, separate regions2+/span100lines+, a selected
recognizable bounded failure block and selected lines at most half the bounding
region. Default15% rendered reduction and all source/descriptor/coordinate/output
checks remain. This profile does not prove semantic completeness or compare
against optimal ordinary search. Exceeding any guard withholds all raw output.
Use targeted reading after rejection; never repeat unchanged calls or escalate
automatically to cloud. Success returns the exact existing numbered CLI packet.

## Disconnect and rollback

```sh
python3 scripts/install.py disconnect-codex --dest "$HOME/.agents/skills/token-router"
python3 scripts/install.py restore --dest "$HOME/.agents/skills/token-router" --backup /verified/backup
python3 scripts/install.py uninstall --dest "$HOME/.agents/skills/token-router"
```

Uninstall removes an unchanged managed connection first; changed settings block
removal so they can be preserved. Disconnect before restoring a21-file version;
its adapter does not exist.22-file updates preserve the managed connection.
Backups stay outside skill discovery, and exact inventories are restored.
Restart/new session is required after rollback as well.

The older I/O-free `routing_policy.plan_activation` native-guide host API remains
available, unchanged and optional. It is not the default connection used above;
its2.7.1 native-only contract and measurement are historical. [Current evaluation](automatic-tool-review/report.ko.md).
