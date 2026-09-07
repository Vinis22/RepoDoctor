import json
from pathlib import Path
from typing import List, Optional

from repodoctor.config import Config
from repodoctor.gitutils import days_since_last_commit, is_git_repo
from repodoctor.models import Check

LINT_FORMAT_CONFIGS = [
    ".flake8",
    ".pylintrc",
    ".eslintrc",
    ".eslintrc.json",
    ".eslintrc.js",
    ".prettierrc",
    ".prettierrc.json",
    "ruff.toml",
    ".ruff.toml",
    "tox.ini",
]
CI_PATHS = [
    ".github/workflows",
    ".gitlab-ci.yml",
    ".circleci/config.yml",
    "azure-pipelines.yml",
    ".drone.yml",
]


def _has_test_command(repo_path: Path) -> bool:
    makefile = repo_path / "Makefile"
    if makefile.exists():
        content = makefile.read_text(encoding="utf-8", errors="ignore")
        if "test:" in content:
            return True

    package_json = repo_path / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8", errors="ignore"))
            if "test" in data.get("scripts", {}):
                return True
        except json.JSONDecodeError:
            pass

    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore")
        if "[tool.pytest" in content:
            return True

    if (repo_path / "pytest.ini").exists() or (repo_path / "tox.ini").exists():
        return True

    return False


def _has_lint_or_format_config(repo_path: Path) -> bool:
    if any((repo_path / name).exists() for name in LINT_FORMAT_CONFIGS):
        return True
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore")
        if "[tool.ruff]" in content or "[tool.black]" in content or "[tool.flake8]" in content:
            return True
    package_json = repo_path / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8", errors="ignore"))
            if "eslintConfig" in data or "prettier" in data:
                return True
        except json.JSONDecodeError:
            pass
    return False


def _has_ci_config(repo_path: Path) -> bool:
    for ci_path in CI_PATHS:
        target = repo_path / ci_path
        if target.is_dir():
            if any(target.glob("*.yml")) or any(target.glob("*.yaml")):
                return True
        elif target.exists():
            return True
    return False


def _find_large_files(repo_path: Path, config: Config) -> List[str]:
    max_bytes = config.max_file_size_mb * 1024 * 1024
    large_files = []
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        relative = str(path.relative_to(repo_path))
        if config.is_ignored(relative):
            continue
        if config.is_check_excepted("quality.large_files", relative):
            continue
        try:
            if path.stat().st_size > max_bytes:
                large_files.append(relative)
        except OSError:
            continue
    return large_files


def run(repo_path: Path, config: Config) -> List[Check]:
    checks: List[Check] = []

    checks.append(
        Check(
            id="quality.test_command",
            category="quality",
            severity="warning",
            passed=_has_test_command(repo_path),
            message="Test command configured",
        )
    )

    checks.append(
        Check(
            id="quality.lint_config",
            category="quality",
            severity="warning",
            passed=_has_lint_or_format_config(repo_path),
            message="Lint/format configuration present",
        )
    )

    checks.append(
        Check(
            id="quality.ci_config",
            category="quality",
            severity="warning",
            passed=_has_ci_config(repo_path),
            message="Local CI configuration present",
        )
    )

    if is_git_repo(repo_path):
        days: Optional[int] = days_since_last_commit(repo_path)
        recent = days is not None and days <= config.recent_commit_days
        message = (
            f"Last commit {days} day(s) ago"
            if days is not None
            else "Could not determine last commit date"
        )
        checks.append(
            Check(
                id="quality.recent_commits",
                category="quality",
                severity="warning",
                passed=recent,
                message=message,
            )
        )
    else:
        checks.append(
            Check(
                id="quality.recent_commits",
                category="quality",
                severity="warning",
                passed=True,
                message="Not a git repository, skipping recent commit check",
                skipped=True,
            )
        )

    large_files = _find_large_files(repo_path, config)
    checks.append(
        Check(
            id="quality.large_files",
            category="quality",
            severity="warning",
            passed=not large_files,
            message=(
                "No oversized files found"
                if not large_files
                else f"{len(large_files)} file(s) larger than {config.max_file_size_mb} MB"
            ),
            details=large_files,
        )
    )

    return [c for c in checks if not config.is_check_excepted(c.id)]
