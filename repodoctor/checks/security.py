import re
from pathlib import Path
from typing import List, Optional

from repodoctor.config import Config
from repodoctor.gitutils import tracked_files
from repodoctor.models import Check

SENSITIVE_FILENAMES = [".pem", "id_rsa", "credentials.json", "secrets.yml", ".p12"]

SECRET_PATTERNS = [
    ("password", re.compile(r"password\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE)),
    ("secret", re.compile(r"secret\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE)),
    ("api_key", re.compile(r"api[_-]?key\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE)),
    ("token", re.compile(r"token\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE)),
    ("connection_string", re.compile(r"://[^\s:/'\"]+:[^\s@/'\"]+@")),
]

PLACEHOLDER_VALUES = {
    "", "changeme", "xxx", "todo", "placeholder", "example", "your_password",
    "your-password", "<password>", "null", "none", "false", "true",
}

TEXT_FILE_MAX_BYTES = 512 * 1024
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".woff", ".woff2", ".ttf"}


def _is_placeholder(value: str) -> bool:
    stripped = value.strip("'\"")
    if stripped.lower() in PLACEHOLDER_VALUES:
        return True
    if stripped.startswith("${") or stripped.startswith("$("):
        return True
    if "os.environ" in stripped or "process.env" in stripped:
        return True
    return False


def _is_gitignored(repo_path: Path, name: str) -> bool:
    gitignore = repo_path / ".gitignore"
    if not gitignore.exists():
        return False
    for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.strip("/") == name or line == f"{name}" or line == f"/{name}":
            return True
    return False


def _candidate_files(repo_path: Path, config: Config, tracked: Optional[List[str]]) -> List[Path]:
    if tracked is not None:
        return [repo_path / f for f in tracked]

    candidates = []
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        relative = str(path.relative_to(repo_path))
        if config.is_ignored(relative):
            continue
        candidates.append(path)
    return candidates


def _scan_secrets(files: List[Path], repo_path: Path, config: Config) -> List[str]:
    findings = []
    for path in files:
        if not path.exists() or not path.is_file():
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            if path.stat().st_size > TEXT_FILE_MAX_BYTES:
                continue
        except OSError:
            continue

        relative = str(path.relative_to(repo_path))
        if config.is_check_excepted("security.secrets_in_files", relative):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            for name, pattern in SECRET_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                value = match.group(1) if match.groups() else ""
                if value and _is_placeholder(value):
                    continue
                findings.append(f"{relative}:{line_number} ({name})")
    return findings


def _scan_compose_passwords(repo_path: Path, config: Config) -> List[str]:
    findings = []
    for name in ["docker-compose.yml", "docker-compose.yaml"]:
        compose_path = repo_path / name
        if not compose_path.exists():
            continue
        if config.is_check_excepted("security.compose_passwords", name):
            continue
        content = compose_path.read_text(encoding="utf-8", errors="ignore")
        pattern = re.compile(r"([A-Z0-9_]*PASSWORD[A-Z0-9_]*)\s*[:=]\s*['\"]?([^\s'\"]+)", re.IGNORECASE)
        for line_number, line in enumerate(content.splitlines(), start=1):
            match = pattern.search(line)
            if not match:
                continue
            value = match.group(2)
            if _is_placeholder(value):
                continue
            findings.append(f"{name}:{line_number}")
    return findings


def run(repo_path: Path, config: Config) -> List[Check]:
    checks: List[Check] = []
    tracked = tracked_files(repo_path)

    env_path = repo_path / ".env"
    env_exists = env_path.exists()
    env_gitignored = _is_gitignored(repo_path, ".env")
    checks.append(
        Check(
            id="security.env_gitignored",
            category="security",
            severity="critical",
            passed=(not env_exists) or env_gitignored,
            message=(
                ".env not present"
                if not env_exists
                else (".env is gitignored" if env_gitignored else ".env exists but is not gitignored")
            ),
        )
    )

    if tracked is not None:
        env_tracked = ".env" in tracked
        checks.append(
            Check(
                id="security.env_tracked",
                category="security",
                severity="critical",
                passed=not env_tracked,
                message=".env is tracked by git" if env_tracked else ".env is not tracked by git",
            )
        )

        sensitive_tracked = [
            f for f in tracked if any(f.endswith(suffix) or Path(f).name == suffix for suffix in SENSITIVE_FILENAMES)
        ]
        checks.append(
            Check(
                id="security.sensitive_files_tracked",
                category="security",
                severity="critical",
                passed=not sensitive_tracked,
                message=(
                    "No sensitive files tracked by git"
                    if not sensitive_tracked
                    else f"{len(sensitive_tracked)} sensitive file(s) tracked by git"
                ),
                details=sensitive_tracked,
            )
        )
    else:
        for check_id, label in [
            ("security.env_tracked", ".env tracked check"),
            ("security.sensitive_files_tracked", "sensitive files tracked check"),
        ]:
            checks.append(
                Check(
                    id=check_id,
                    category="security",
                    severity="critical",
                    passed=True,
                    message=f"Not a git repository, skipping {label}",
                    skipped=True,
                )
            )

    candidates = _candidate_files(repo_path, config, tracked)
    secret_findings = _scan_secrets(candidates, repo_path, config)
    checks.append(
        Check(
            id="security.secrets_in_files",
            category="security",
            severity="critical",
            passed=not secret_findings,
            message=(
                "No obvious secrets found in monitored files"
                if not secret_findings
                else f"{len(secret_findings)} possible secret(s) found"
            ),
            details=secret_findings,
        )
    )

    compose_findings = _scan_compose_passwords(repo_path, config)
    checks.append(
        Check(
            id="security.compose_passwords",
            category="security",
            severity="critical",
            passed=not compose_findings,
            message=(
                "No hardcoded passwords found in docker-compose"
                if not compose_findings
                else f"{len(compose_findings)} hardcoded password(s) found in docker-compose"
            ),
            details=compose_findings,
        )
    )

    return [c for c in checks if not config.is_check_excepted(c.id)]
