#!/usr/bin/env python3
"""Run token-router regression tests from a JSON manifest."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = SKILL_ROOT / "scripts" / "router.py"


def load_router_module():
    spec = importlib.util.spec_from_file_location("token_router_under_test", ROUTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load router module from {ROUTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run token-router regression tests.")
    parser.add_argument("manifest", help="Path to router-tests.json")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Call GPT-6 Luna Light through Codex CLI for live selection cases.",
    )
    return parser.parse_args()


def resolve_fixture(manifest_path: Path, raw_fixture: str) -> Path:
    fixture = Path(raw_fixture)
    if fixture.is_absolute():
        return fixture
    return (manifest_path.parent / fixture).resolve()


def line_texts(path: Path, line_numbers: list[int]) -> list[str]:
    wanted = set(line_numbers)
    found: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line_no in wanted:
                found.append(line.rstrip("\n"))
    return found


def run_case(
    case: dict[str, Any],
    manifest_path: Path,
    router_module: Any,
    real: bool,
) -> list[str]:
    errors: list[str] = []
    fixture = resolve_fixture(manifest_path, case["fixture"])
    mode = case["mode"]
    query = case.get("query", "")

    if case.get("prompt_contains"):
        prompt = router_module.build_prompt(
            fixture.read_text(encoding="utf-8", errors="replace"),
            mode,
            query=query,
        )
        for expected in case["prompt_contains"]:
            if expected not in prompt:
                errors.append(f"prompt missing {expected!r}")

    env = os.environ.copy()
    env.setdefault("ROUTER_TIMEOUT", "60")
    env.update(case.get("env", {}))
    env.pop("ROUTER_MOCK_RESPONSE", None)
    if not real and "mock_response" in case:
        env["ROUTER_MOCK_RESPONSE"] = json.dumps(case["mock_response"])

    cmd = [sys.executable, str(ROUTER_PATH), mode, str(fixture)]
    if query:
        cmd.extend(["--query", query])

    started = time.monotonic()
    result = subprocess.run(
        cmd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed = time.monotonic() - started
    if real:
        print(f"  {elapsed:.2f}s")
        for line in result.stderr.splitlines():
            if line.startswith("[token-router usage]"):
                print("  " + line)
    output = result.stdout + result.stderr
    if result.returncode != case.get("expected_exit", 0):
        errors.append(f"exit {result.returncode}, expected {case.get('expected_exit', 0)}")

    expectations = case.get("real_output_contains", []) if real else case.get("expected_output_contains", [])
    for expected in expectations:
        if expected not in output:
            errors.append(f"output missing {expected!r}")

    for text in line_texts(fixture, case.get("expected_contains_lines", [])):
        if text and text not in output:
            errors.append(f"output missing fixture line {text!r}")

    if case.get("forbid_fallback", True) and ("#### Router Fallback" in output or "deterministic streaming fallback" in output or '"status": "fallback"' in output):
        errors.append("unexpected fallback output")

    return errors


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    cases = json.loads(manifest_path.read_text(encoding="utf-8"))
    router_module = load_router_module()

    failures: list[str] = []
    for case in cases:
        if args.real and case.get("mock_only", False):
            continue
        name = case.get("name", case.get("fixture", "unnamed"))
        errors = run_case(case, manifest_path, router_module, args.real)
        if errors:
            failures.append(f"{name}: {'; '.join(errors)}")
            print(f"[FAIL] {name}")
        else:
            print(f"[OK] {name}")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
