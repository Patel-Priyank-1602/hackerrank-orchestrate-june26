"""
Setup script — creates the hackerrank_orchestrate log directory and log file.
Run this once before starting the pipeline.
"""

import os
from pathlib import Path
from datetime import datetime, timezone

def setup_log():
    home = Path.home()
    log_dir = home / "hackerrank_orchestrate"
    log_file = log_dir / "log.txt"

    log_dir.mkdir(parents=True, exist_ok=True)

    # Check if agreement already recorded
    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        repo_root = str(Path(__file__).resolve().parent.parent)
        if f"AGREEMENT RECORDED: {repo_root}" in content:
            print(f"Agreement already recorded for {repo_root}")
            return

    print(f"Log file: {log_file}")
    print("Log directory created. Ready for onboarding.")

if __name__ == "__main__":
    setup_log()
