#!/usr/bin/env python3
"""
_run_once.py
------------
Internal helper — runs pytest once and prints a JSON summary to stdout.
Called by generate_report.py in a subprocess loop.
"""

import sys, json, time, pathlib

_HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(_HERE))

import pytest


class _Collector:
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def pytest_sessionstart(self, session):
        self.start_time = time.time()

    def pytest_sessionfinish(self, session):
        self.end_time = time.time()

    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            return
        self.total += 1
        parts = report.nodeid.split("::")
        class_name = parts[-2] if len(parts) >= 2 else "Unknown"
        test_name = parts[-1]

        cat_map = {
            "TestColdStart": "A. Cold Start",
            "TestFilterCriteria": "B. Filter Criteria",
            "TestLlmOutputFormat": "C. LLM Output Format",
            "TestLatencyAndStress": "D. Latency / Stress",
            "TestInvalidInput": "E. Invalid Input",
            "TestSessionAndGuardrails": "F. Session & Guardrails",
        }
        category = cat_map.get(class_name, "Other")

        status = "PASSED"
        if report.passed:
            self.passed += 1
        elif report.failed:
            status = "FAILED"
            self.failed += 1
        elif report.skipped:
            status = "SKIPPED"
            self.skipped += 1

        duration = getattr(report, "duration", 0.0)
        longrepr = str(report.longrepr) if report.longrepr else ""

        test_input = test_name.replace("test_tc", "").replace("_", " ").strip()
        test_input = "".join(c for c in test_input if not c.isdigit()).strip()

        self.results.append({
            "test_id": test_name,
            "category": category,
            "input": test_input,
            "status": status,
            "duration": round(duration, 4),
            "notes": longrepr,
            "class_name": class_name,
        })


if __name__ == "__main__":
    collector = _Collector()
    test_file = str(_HERE / "tests" / "test_recommendation_agent.py")
    args = [test_file, "-k", "not Integration", "--tb=short", "--no-header", "-q"]
    exit_code = pytest.main(args, plugins=[collector])
    total_s = round((collector.end_time or time.time()) - (collector.start_time or time.time()), 2)

    output = {
        "exit_code": exit_code,
        "total": collector.total,
        "passed": collector.passed,
        "failed": collector.failed,
        "skipped": collector.skipped,
        "duration_s": total_s,
        "results": collector.results,
    }
    json.dump(output, sys.stdout)
    sys.exit(exit_code)
