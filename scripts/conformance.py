#!/usr/bin/env python3
"""Run the public OAFF fixture corpus against an external verifier command.

This runner never imports the OAFF verifier. The implementation under test
must emit one JSON report with status and diagnostics, as documented below.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))


def _report(stdout: str) -> dict:
    value = json.loads(stdout)
    if isinstance(value, list):
        if len(value) != 1:
            raise ValueError("expected exactly one JSON report")
        value = value[0]
    if not isinstance(value, dict):
        raise ValueError("JSON report must be an object")
    return value


def run(command: list[str]) -> tuple[int, int]:
    if not command or not any("{file}" in part for part in command):
        raise ValueError("command must contain a {file} argument placeholder")
    cases = [(path, None) for path in MANIFEST["valid"]]
    cases += list(MANIFEST["invalid"].items())
    passed = 0
    for relative, invalid_code in cases:
        path = FIXTURES / relative
        argv = [part.replace("{file}", str(path)) for part in command]
        try:
            completed = subprocess.run(argv, capture_output=True, text=True,
                                       timeout=30, check=False)
            report = _report(completed.stdout)
            if invalid_code is None:
                correct = (completed.returncode == 0 and
                           report.get("status") in {"valid", "valid_with_limits"} and
                           report.get("integrity") == "pass" and
                           report.get("local_authority") in {"not_evaluated", "none"})
            else:
                codes = {item.get("code") for item in report.get("diagnostics", [])
                         if isinstance(item, dict)}
                correct = (completed.returncode == 1 and
                           report.get("status") == "invalid" and
                           invalid_code in codes)
            detail = "" if correct else f"exit={completed.returncode}, report={report}"
        except (OSError, subprocess.TimeoutExpired, ValueError, json.JSONDecodeError) as exc:
            correct, detail = False, str(exc)
        print(f"{'PASS' if correct else 'FAIL'} {relative}{': ' + detail if detail else ''}")
        passed += int(correct)
    return passed, len(cases)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run OAFF v0.1 fixtures against a verifier; use {file} as the path argument"
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        passed, total = run(command)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"{passed}/{total} conformance cases passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
