import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def init_git_repo(path: Path):
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@repodoctor.local"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "RepoDoctor Test"], cwd=path, check=True, capture_output=True)


def commit_all(path: Path, message: str = "test commit"):
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=path, check=True, capture_output=True)
