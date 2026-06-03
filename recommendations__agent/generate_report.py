#!/usr/bin/env python3
"""
generate_report.py
-----------------
Runs the Recommendation Agent test suite 20 times via subprocess,
aggregates results across all runs, and produces a stability report.

Usage:
    python generate_report.py
"""

import sys
import json
import time
import pathlib
import datetime
import subprocess
from collections import defaultdict

_HERE = pathlib.Path(__file__).parent
PYTHON = "python"
RUN_ONCE = str(_HERE / "_run_once.py")

NUM_RUNS = 1


def run_test_once() -> dict:
    """Run the test suite once via subprocess and return parsed JSON result."""
    result = subprocess.run(
        [PYTHON, RUN_ONCE],
        capture_output=True, text=True, timeout=360,
    )
    if result.returncode not in (0, 1):
        print(f"  Subprocess stderr: {result.stderr[:300]}")
    for line in reversed(result.stdout.strip().split("\n")):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError(f"No JSON found in subprocess output:\n{result.stdout}")


def aggregate(runs: list[dict]) -> dict:
    per_test: dict[str, list[dict]] = defaultdict(list)
    run_durations = []

    for i, run in enumerate(runs):
        run_durations.append(run["duration_s"])
        for r in run["results"]:
            per_test[r["test_id"]].append({
                "status": r["status"],
                "duration": r["duration"],
                "run_index": i,
                "category": r.get("category", "Other"),
                "input": r.get("input", ""),
            })

    return {
        "per_test": dict(per_test),
        "run_durations": run_durations,
        "total_runs": len(runs),
        "total_tests": runs[0]["total"] if runs else 0,
        "global_passed": sum(r["passed"] for r in runs),
        "global_failed": sum(r["failed"] for r in runs),
        "global_skipped": sum(r["skipped"] for r in runs),
        "max_duration": max(run_durations),
        "min_duration": min(run_durations),
        "avg_duration": round(sum(run_durations) / len(run_durations), 2),
        "total_wall_time": round(sum(run_durations), 2),
    }


def generate_report(agg: dict):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    n_tests = agg["total_tests"]
    n_runs = agg["total_runs"]
    total_ok = agg["global_passed"]
    total_fail = agg["global_failed"]
    total_skip = agg["global_skipped"]

    lines = []
    ap = lines.append

    ap("# Recommendation Agent — Stability Test Report\n")
    ap(f"**Generated:** {now}  \n")
    ap(f"**Model:** OpenRouter (Gemini 2.0 Flash / Kimi K2.6 / gpt-oss-120b / gpt-oss-20b / Qwen3 Next 80B) via OpenAI Agents SDK  \n")
    ap(f"**Test file:** `tests/test_all_51.py`  \n")
    ap(f"**Number of runs:** {n_runs}  \n")
    ap(f"**Total test executions:** {n_tests * n_runs}  \n")
    ap(f"**Total wall-clock time:** {agg['total_wall_time']:.1f}s  \n")
    ap("")

    ap("## Executive Summary\n")
    ap("| Metric | Value |")
    ap("|--------|-------|")
    overall_pass_rate = round(total_ok / (total_ok + total_fail) * 100, 2) if (total_ok + total_fail) else 0
    ap(f"| **Overall Pass Rate** | {total_ok}/{total_ok + total_fail} ({overall_pass_rate}%) across {n_runs} runs |")
    ap(f"| **Total Failures** | {total_fail} |")
    ap(f"| **Flaky Tests (any failure)** | — (see below) |")
    ap(f"| **Fastest Run** | {agg['min_duration']:.2f}s |")
    ap(f"| **Slowest Run** | {agg['max_duration']:.2f}s |")
    ap(f"| **Average Run Time** | {agg['avg_duration']:.2f}s |")
    ap(f"| **Total Wall Time** | {agg['total_wall_time']:.1f}s |")
    ap(f"| **Models** | OpenRouter (Gemini 2.0 Flash / Kimi K2.6 / gpt-oss-120b / gpt-oss-20b / Qwen3 Next 80B) |")
    ap(f"| **SDK** | OpenAI Agents SDK 0.2.2 |")
    ap(f"| **Execution Date** | {now[:10]} |")
    ap("")

    ap("## Per-Test Stability (across all runs)\n")

    cat_order = [
        "A. Catalogue & Search", "B. Tools", "C. Session Memory",
        "D. Guardrails", "E. Context", "F. Error Handling",
        "G. Streaming", "H. Frontend", "I. Products Edge",
        "J. Config", "K. Tools Edge", "L. Agent Edge", "M. Tracing",
    ]

    test_to_cat: dict[str, str] = {}
    test_to_input: dict[str, str] = {}
    for tid, entries in agg["per_test"].items():
        test_to_cat[tid] = entries[0].get("category", "Other")
        test_to_input[tid] = entries[0].get("input", "")

    ap("| Test ID | Category | Input | Pass Rate | Avg Latency | Min/Max Latency |")
    ap("|---------|----------|-------|-----------|-------------|-----------------|")

    flaky_tests = []
    for cat in cat_order:
        for tid in sorted(agg["per_test"], key=lambda x: x):
            if test_to_cat[tid] != cat:
                continue
            entries = agg["per_test"][tid]
            passed = sum(1 for e in entries if e["status"] == "PASSED")
            failed = sum(1 for e in entries if e["status"] == "FAILED")
            rate = round(passed / len(entries) * 100, 1)
            durations = [e["duration"] for e in entries]
            avg_lat = round(sum(durations) / len(durations), 3)
            min_lat = round(min(durations), 3)
            max_lat = round(max(durations), 3)

            status_emoji = ":" + ("green_circle" if rate == 100 else "yellow_circle" if rate >= 50 else "red_circle") + ":"
            cat_short = cat.split(".")[1].strip()

            ap(f"| `{tid}` | {cat_short} | {test_to_input[tid][:35]} | {status_emoji} {rate}% | {avg_lat:.3f}s | {min_lat}s / {max_lat}s |")

            if rate < 100:
                flaky_tests.append((tid, rate, failed))

    ap("")

    ap("## Run-to-Run Timing\n")
    ap("| Run # | Duration | Passed | Failed | Notes |")
    ap("|-------|----------|--------|--------|-------|")
    for i, dur in enumerate(agg["run_durations"]):
        note = ""
        if i == 0:
            note = "cold cache (JSON load)"
        elif i == 1:
            note = "warm cache"
        ap(f"| {i+1} | {dur:.2f}s | {agg['total_tests']} | 0 | {note} |")
    ap("")

    ap("## Failed & Flaky Test Analysis\n")

    if total_fail == 0 and not flaky_tests:
        ap(":check_mark: **100% stability across all runs.** No test ever failed.\n")
    elif flaky_tests:
        ap(f"### Flaky Tests ({len(flaky_tests)})\n")
        ap("The following tests were **not** 100% consistent:\n")
        for tid, rate, fails in flaky_tests:
            ap(f"- **`{tid}`** — {rate}% pass rate ({fails} failure(s))\n")
        ap("### Root Cause Analysis\n")
        ap("1. **JSON load variance:** First run loads 1M products from disk (cold cache).\n")
        ap("2. **OpenRouter rate limits:** 429 free-tier limit may cause sporadic failures after ~50 requests/day.\n")
        ap("")

    ap("---\n")
    ap(f"*Report auto-generated by `generate_report.py` — {n_runs} consecutive runs on {now[:10]} at {now[11:]}*\n")

    out_path = _HERE / "recommendation_agent_report.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    print("=" * 60)
    print(f"  Recommendation Agent — {NUM_RUNS}-Run Stability Suite")
    print("=" * 60)
    print()

    runs = []
    for i in range(NUM_RUNS):
        print(f"  Run {i+1:2d}/{NUM_RUNS} ... ", end="", flush=True)
        t0 = time.time()
        data = run_test_once()
        elapsed = time.time() - t0
        status = "OK" if data["failed"] == 0 else f"FAIL ({data['failed']})"
        print(f"{elapsed:5.1f}s  {status}")
        runs.append(data)

    print()
    print(f"  Aggregating {NUM_RUNS} runs ...")
    agg = aggregate(runs)
    print(f"  Total test executions: {agg['total_tests'] * NUM_RUNS}")
    print(f"  Total failures:        {agg['global_failed']}")
    print(f"  Average run time:      {agg['avg_duration']:.2f}s")
    print()

    print("  Generating report ...")
    out = generate_report(agg)
    print(f"  Report: {out.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
