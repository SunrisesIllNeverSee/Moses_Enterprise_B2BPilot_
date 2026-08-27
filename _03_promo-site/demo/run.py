#!/usr/bin/env python3
"""
MO§ES™ Demo Runner — one-liner entry point.

Usage:
  curl -sL https://mos2es.org/demo/run.py | python3 -

Or if you have the repo cloned:
  cd Moses_Enterprise_B2BPilot_/_01_platform
  python3 -m src.cli.main demo full

This script clones the repo to a temp directory, installs the one
dependency (rich), and runs the full 10-step demo pipeline.
Requires Python 3.10+ and git.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_URL = "https://github.com/SunrisesIllneverSee/Moses_Enterprise_B2BPilot_.git"
REPO_DIR = "Moses_Enterprise_B2BPilot_"
PLATFORM_DIR = "Moses_Enterprise_B2BPilot_/_01_platform"


def main():
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10+ required. You have", sys.version)
        sys.exit(1)

    # Check git is available
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: git is required but not found in PATH.")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        print(f"Cloning MO§ES™ repo to {tmpdir}/{REPO_DIR}...")
        print()
        result = subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, REPO_DIR],
            capture_output=False,
        )
        if result.returncode != 0:
            print()
            print("ERROR: Could not clone the repository.")
            print("The repo may be private. If so, clone it manually:")
            print(f"  git clone {REPO_URL}")
            print(f"  cd {PLATFORM_DIR}")
            print(f"  pip install rich")
            print(f"  python3 -m src.cli.main demo full")
            sys.exit(1)

        platform_path = Path(tmpdir) / PLATFORM_DIR
        os.chdir(platform_path)

        # Install the one dependency
        print()
        print("Installing rich (the only dependency)...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "rich", "--quiet"],
            capture_output=True,
        )

        # Run the demo
        print()
        print("=" * 60)
        print("  MO§ES™ DEMO — 10-step operator evaluation pipeline")
        print("=" * 60)
        print()

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "demo", "full"],
            cwd=platform_path,
        )

        print()
        if result.returncode == 0:
            print("Demo complete. Outputs are in demo_data/graphics/.")
            print()
            print("To explore individual commands:")
            print("  python3 -m src.cli.main --help")
            print("  python3 -m src.cli.main score operator op_001")
            print("  python3 -m src.cli.main compare operator-system")
            print("  python3 -m src.cli.main lineage show op_046")
            print()
            print("To run the test suite:")
            print("  python3 -m pytest tests/ -q")
            print()
            print("To start the MCP server:")
            print("  pip install mcp && python3 -m src.mcp_server.server")

        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
