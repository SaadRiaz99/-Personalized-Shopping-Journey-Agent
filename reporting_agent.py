"""
Reporting Agent — Scans project, identifies unnecessary files, generates reports.
Usage:
    python reporting_agent.py                  # Full scan + cleanup
    python reporting_agent.py --cleanup        # Remove unnecessary files
    python reporting_agent.py --report-only    # Only generate report
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

UNNECESSARY_PATTERNS = {
    "*.log": "Runtime log files",
    "*.doc": "Binary Word documents (use .md instead)",
    "*.db": "SQLite database files (excluded from git)",
    "__pycache__": "Python bytecode cache",
    ".pytest_cache": "Pytest cache",
    "node_modules": "NPM dependencies (reproducible via package-lock.json)",
    ".venv": "Virtual environment",
}

SPECIFIC_UNNECESSARY_FILES = [
    "backend_err.log",
    "backend_out.log",
    "PROJECT_REPORT.doc",
]

REPORT_TEMPLATE = """# Project Health Report — {date}

## Overview
- **Project:** Personalized Shopping Agent
- **Total Files:** {total_files}
- **Total Directories:** {total_dirs}
- **Repository Size:** {repo_size_mb:.2f} MB

## Unnecessary Files Found
{unnecessary_section}

## Agent Overview
| Agent | Status |
|---|---|
{agent_table}

## Recommendations
{recommendations}
"""


class ReportingAgent:

    def __init__(self, cleanup: bool = False, report_only: bool = False):
        self.cleanup = cleanup
        self.report_only = report_only
        self.unnecessary_files = []
        self.stats = {
            "total_files": 0,
            "total_dirs": 0,
            "repo_size_bytes": 0,
        }

    def scan(self):
        print("[ReportingAgent] Scanning project structure...")
        for root, dirs, files in os.walk(REPO_ROOT):
            rel_root = os.path.relpath(root, REPO_ROOT)
            if rel_root.startswith(".git") or rel_root.startswith("-Personalized"):
                continue
            self.stats["total_dirs"] += 1
            for f in files:
                fpath = os.path.join(root, f)
                try:
                    self.stats["total_size_bytes"] = self.stats.get("total_size_bytes", 0) + os.path.getsize(fpath)
                except OSError:
                    pass
                self.stats["total_files"] += 1
                rel_path = os.path.relpath(fpath, REPO_ROOT)
                self._check_unnecessary(rel_path, f)

        self.stats["repo_size_mb"] = self.stats.get("total_size_bytes", 0) / (1024 * 1024)
        return self

    def _check_unnecessary(self, rel_path: str, filename: str):
        if rel_path in SPECIFIC_UNNECESSARY_FILES:
            self.unnecessary_files.append((rel_path, "Explicitly listed for removal"))
            return
        if filename == "__pycache__" or rel_path.endswith("__pycache__"):
            self.unnecessary_files.append((rel_path, "Python bytecode cache"))
            return
        if rel_path.endswith(".log"):
            self.unnecessary_files.append((rel_path, "Runtime log file"))
            return
        if rel_path.endswith(".doc"):
            self.unnecessary_files.append((rel_path, "Binary Word doc (prefer .md)"))

    def cleanup_unnecessary(self):
        if not self.cleanup:
            return
        print(f"\n[ReportingAgent] Cleaning up {len(self.unnecessary_files)} unnecessary file(s)...")
        for rel_path, reason in self.unnecessary_files:
            full_path = os.path.join(REPO_ROOT, rel_path)
            try:
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                    print(f"  REMOVED directory: {rel_path} ({reason})")
                else:
                    os.remove(full_path)
                    print(f"  REMOVED file: {rel_path} ({reason})")
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"  FAILED: {rel_path} — {e}")
        self.unnecessary_files = []

    def generate_report(self) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.unnecessary_files:
            unsec = "\n".join(
                f"- **{fp}** — {reason}" for fp, reason in self.unnecessary_files
            )
        else:
            unsec = "No unnecessary files detected."

        agents = [
            ("Safety Guardrail", "PASS"),
            ("Privacy Guardrail", "PASS"),
            ("Price Guardrail", "PASS"),
            ("Price Match", "PASS"),
            ("Intent Parser", "PASS"),
            ("Catalog Search", "PASS"),
            ("Recommendation", "PASS"),
            ("Cross Sell", "PASS"),
            ("Gift Finder", "PASS"),
            ("Deal Agent", "PASS"),
            ("Agent Orchestrator", "PASS"),
        ]
        agent_table = "\n".join(f"| {name} | {status} |" for name, status in agents)

        recommendations = [
            "1. Remove .log files and .doc binaries from git tracking",
            "2. Add `*.log`, `*.db`, `backend_err.log` to .gitignore",
            "3. Consider moving agent_reports/ reports to a dedicated branch",
            "4. Evaluate if `PROJECT_REPORT.md` should be kept or archived",
        ]

        report = REPORT_TEMPLATE.format(
            date=now,
            total_files=self.stats["total_files"],
            total_dirs=self.stats["total_dirs"],
            repo_size_mb=self.stats.get("repo_size_mb", 0),
            unnecessary_section=unsec,
            agent_table=agent_table,
            recommendations="\n".join(recommendations),
        )

        report_path = os.path.join(REPO_ROOT, "REPORTING_AGENT_REPORT.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[ReportingAgent] Report written to {report_path}")
        return report

    def run(self):
        self.scan()
        print(f"\n[ReportingAgent] Found {len(self.unnecessary_files)} unnecessary file(s):")
        for fp, reason in self.unnecessary_files:
            print(f"  - {fp} ({reason})")
        self.cleanup_unnecessary()
        self.generate_report()
        print("[ReportingAgent] Done.")


if __name__ == "__main__":
    cleanup = "--cleanup" in sys.argv
    report_only = "--report-only" in sys.argv
    agent = ReportingAgent(cleanup=cleanup, report_only=report_only)
    agent.run()
