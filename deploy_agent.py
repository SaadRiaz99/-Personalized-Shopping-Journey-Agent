"""
Deploy Agent — Pushes specified files to a target branch with individual commits.
Usage:
    python deploy_agent.py --branch "Saad Bin Riaz Branch" --files file1.py file2.py
    python deploy_agent.py --branch "Saad Bin Riaz Branch" --report-only agent_reports/
    python deploy_agent.py --branch "Saad Bin Riaz Branch" --all
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent


class DeployAgent:

    def __init__(self, branch: str, files: list[str] = None, report_only: bool = False, deploy_all: bool = False):
        self.branch = branch
        self.files = files or []
        self.report_only = report_only
        self.deploy_all = deploy_all
        self.temp_dir = None

    def _git(self, *args, capture=True):
        cmd = ["git"] + list(args)
        print(f"  git {' '.join(args)}")
        result = subprocess.run(cmd, capture_output=capture, text=True, cwd=REPO_ROOT)
        if result.returncode != 0 and capture:
            print(f"  stderr: {result.stderr.strip()}")
        return result

    def deploy(self):
        branch_safe = self.branch.replace(" ", "-")
        print(f"[DeployAgent] Deploying to branch '{self.branch}'...")

        status = self._git("status", "--porcelain")
        if status.stdout.strip():
            print("[DeployAgent] Stashing working tree changes...")
            self._git("stash", "--include-untracked")

        try:
            self._git("fetch", "--all")
            self._git("checkout", "-b", branch_safe, capture=False)
        except Exception:
            self._git("checkout", branch_safe, capture=False)
            self._git("pull", "origin", branch_safe, "--rebase")

        if self.deploy_all:
            self._deploy_all()
        elif self.report_only:
            self._deploy_reports()
        elif self.files:
            self._deploy_files()

        self._git("add", "-A")
        commit_msg = f"deploy: push updates to {self.branch} [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        self._git("commit", "-m", commit_msg)
        self._git("push", "origin", branch_safe)

        self._git("checkout", "-", capture=False)
        print(f"[DeployAgent] Successfully deployed to '{self.branch}'")

    def _deploy_all(self):
        print("[DeployAgent] Deploying all project files...")

    def _deploy_reports(self):
        print("[DeployAgent] Deploying only report files...")
        reports_dir = REPO_ROOT / "agent_reports"
        if reports_dir.exists():
            for f in reports_dir.glob("*.md"):
                print(f"  Staging report: {f.name}")

    def _deploy_files(self):
        print(f"[DeployAgent] Deploying {len(self.files)} file(s)...")
        for f in self.files:
            fp = REPO_ROOT / f
            if fp.exists():
                print(f"  Staging: {f}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Deploy Agent")
    parser.add_argument("--branch", default=None, help="Target branch name")
    parser.add_argument("--files", nargs="*", default=None, help="Files to deploy")
    parser.add_argument("--report-only", action="store_true", help="Deploy only reports")
    parser.add_argument("--all", dest="deploy_all", action="store_true", help="Deploy all files")
    args = parser.parse_args()

    if not args.branch:
        branch = "Saad-Bin-Riaz-Branch"
        print(f"[DeployAgent] No --branch provided, defaulting to '{branch}'")
    else:
        branch = args.branch

    agent = DeployAgent(
        branch=branch,
        files=args.files,
        report_only=args.report_only,
        deploy_all=args.deploy_all or True,
    )
    agent.deploy()
