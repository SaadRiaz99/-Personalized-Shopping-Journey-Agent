import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def pytest_sessionfinish(session, exitstatus):
    try:
        import importlib
        mod = importlib.import_module("test_agents_individual")
        if hasattr(mod, "_generate_reports"):
            mod._generate_reports()
    except Exception as e:
        print(f"Report generation skipped: {e}")
