import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def is_git_repo(repo_path: Path) -> bool:
    return (repo_path / ".git").exists()


def _run_git(repo_path: Path, args: List[str]) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path)] + args,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def tracked_files(repo_path: Path) -> Optional[List[str]]:
    if not is_git_repo(repo_path):
        return None
    output = _run_git(repo_path, ["ls-files"])
    if output is None:
        return None
    return [line for line in output.splitlines() if line.strip()]


def last_commit_datetime(repo_path: Path) -> Optional[datetime]:
    if not is_git_repo(repo_path):
        return None
    output = _run_git(repo_path, ["log", "-1", "--format=%ct"])
    if not output or not output.strip():
        return None
    timestamp = int(output.strip())
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def days_since_last_commit(repo_path: Path) -> Optional[int]:
    last = last_commit_datetime(repo_path)
    if last is None:
        return None
    delta = datetime.now(timezone.utc) - last
    return delta.days
