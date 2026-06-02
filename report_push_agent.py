"""
Report Push Agent — Pushes each report as an individual commit to a target branch.
Usage:
    python report_push_agent.py --branch "Saad Bin Riaz Branch"
    python report_push_agent.py --branch "Saad Bin Riaz Branch" --reports-dir agent_reports/
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent


class ReportPushAgent:

    def __init__(self, branch: str, reports_dir: str = "agent_reports"):
        self.branch = branch
        self.branch_safe = branch.replace(" ", "-")
        self.reports_dir = REPO_ROOT / reports_dir
        self.committed = []
        self.skipped = []

    def _git(self, *args, capture=True):
        cmd = ["git"] + list(args)
        result = subprocess.run(cmd, capture_output=capture, text=True, cwd=REPO_ROOT)
        if result.returncode != 0 and capture:
            print(f"  stderr: {result.stderr.strip()}")
        return result

    def push(self):
        print(f"[ReportPushAgent] Pushing reports to '{self.branch}'...")

        stash_result = self._git("stash", "--include-untracked")
        had_changes = "Saved working directory" in stash_result.stdout

        try:
            existing = self._git("rev-parse", "--verify", self.branch_safe)
            if existing.returncode == 0:
                self._git("checkout", self.branch_safe, capture=False)
                self._git("pull", "origin", self.branch_safe, "--rebase")
            else:
                self._git("checkout", "-b", self.branch_safe, capture=False)

            if not self.reports_dir.exists():
                print(f"[ReportPushAgent] Reports directory not found: {self.reports_dir}")
                return

            report_files = sorted(self.reports_dir.glob("*.md"))

            for rp in report_files:
                report_name = rp.stem.replace("_", " ").title()
                dest = self.reports_dir / rp.name

                self._git("checkout", "origin/main", "--", str(dest), capture=False)
                if not dest.exists():
                    print(f"  SKIP (not on main): {rp.name}")
                    self.skipped.append(rp.name)
                    continue

                self._git("add", str(dest))
                commit_msg = f"report: add {report_name} [{rp.stem}]"
                self._git("commit", "-m", commit_msg)
                print(f"  COMMITTED: {rp.name}")
                self.committed.append(rp.name)

        finally:
            if had_changes:
                self._git("checkout", "-", capture=False)
                self._git("stash", "pop")

        if self.committed:
            self._git("push", "origin", self.branch_safe)
            print(f"[ReportPushAgent] Pushed {len(self.committed)} report(s) to '{self.branch}'")
        else:
            print("[ReportPushAgent] No reports to push.")

        print(f"\nSummary:")
        print(f"  Committed: {len(self.committed)}")
        print(f"  Skipped:   {len(self.skipped)}")
        for name in self.committed:
            print(f"    + {name}")
        for name in self.skipped:
            print(f"    - {name}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Report Push Agent")
    parser.add_argument("--branch", default="Saad Bin Riaz Branch", help="Target branch")
    parser.add_argument("--reports-dir", default="agent_reports", help="Directory containing report markdown files")
    args = parser.parse_args()

    agent = ReportPushAgent(branch=args.branch, reports_dir=args.reports_dir)
    agent.push()
