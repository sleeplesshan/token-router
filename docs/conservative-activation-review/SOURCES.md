# Sources and reproducibility

This review reuses known CPython/SciPy log and pandas code snapshots. It is a regression evaluation, not independent holdout evidence. Source bytes/hashes, explicit selectors, fixed answers and accepted evidence are in manifest.json; prompts and instructions were locked before any new main turn. Original v2.7 scores and manifests were not overwritten.

Pinned upstream locations and third-party notices: [actual-reader SOURCES](../actual-reader-review/SOURCES.md). The visible-summary task uses the same SciPy snapshot and is not a separate source family. Repeats and translated questions are not independent projects. Source bodies are not duplicated here.

The local reproduction directory was `/Users/han/Documents/Token/benchmarks/activation-harness-20261013`. `python3 prepare.py`, `python3 test_client.py`, `python3 run.py`, `python3 offline.py`, `python3 summarize.py`, then `python3 plot.py` created the locked run and report. Prepare/run are local environment drivers; public native_client.py shows the transport, not a supported standalone product or a global hook. Native app-server0.162.1 with builtin OpenAI ChatGPT login was used. Authenticate normally; no credentials are in evidence.

For another host, copy hash-verified sources into isolated plain/gated workspaces, install the measured payload into only gated/.agents/skills/token-router, disable other skills/tools through session settings, import plan_activation before turn/start, and conditionally attach the native SkillUserInput. Reuse the frozen prompts, rubric,3-command recovery budget and gpt-6.1-sol/medium. The raw event excerpt preserves main commands/answers/cumulative counters, excluding unrelated startup inventory and replacing home paths. raw-hashes.json distinguishes original local logs from public sanitized excerpts.

No new model trial is required to run product unit/manifest/archive checks. A new model experiment must use a fresh output directory and new lock; never replace this evaluation.
