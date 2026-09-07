from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any

import yaml

CONFIG_FILENAME = ".repocheckup.yml"

DEFAULT_IGNORE_PATHS = [
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
]


@dataclass
class Exception_:
    check: str
    path: str = ""


@dataclass
class Config:
    ignore_paths: List[str] = field(default_factory=lambda: list(DEFAULT_IGNORE_PATHS))
    exceptions: List[Exception_] = field(default_factory=list)
    max_file_size_mb: float = 5.0
    recent_commit_days: int = 90

    def is_check_excepted(self, check_id: str, path: str = "") -> bool:
        for exc in self.exceptions:
            if exc.check != check_id:
                continue
            if not exc.path:
                return True
            if path and (exc.path in path or Path(path).match(exc.path)):
                return True
        return False

    def is_ignored(self, relative_path: str) -> bool:
        parts = Path(relative_path).parts
        for ignored in self.ignore_paths:
            ignored_parts = Path(ignored).parts
            if parts[: len(ignored_parts)] == ignored_parts:
                return True
        return False


def load_config(repo_path: Path) -> Config:
    config_path = repo_path / CONFIG_FILENAME
    if not config_path.exists():
        return Config()

    raw: Dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    ignore_paths = list(DEFAULT_IGNORE_PATHS) + list(raw.get("ignore_paths", []))
    exceptions = [
        Exception_(check=item.get("check", ""), path=item.get("path", ""))
        for item in raw.get("exceptions", [])
    ]

    return Config(
        ignore_paths=ignore_paths,
        exceptions=exceptions,
        max_file_size_mb=float(raw.get("max_file_size_mb", 5.0)),
        recent_commit_days=int(raw.get("recent_commit_days", 90)),
    )
