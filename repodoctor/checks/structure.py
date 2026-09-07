from pathlib import Path
from typing import List

from repodoctor.config import Config
from repodoctor.models import Check

DEPENDENCY_MANIFESTS = ["requirements.txt", "pyproject.toml", "package.json"]
LOCKFILES = [
    "poetry.lock",
    "Pipfile.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "uv.lock",
]
TEST_DIRS = ["tests", "test", "spec", "__tests__"]
SCRIPT_EQUIVALENTS = ["Makefile", "makefile", "scripts", "tasks.py", "noxfile.py"]
DOCS_DIRS = ["docs", "doc", "documentation"]
DOCS_SECTION_MARKERS = ["## documentation", "## docs", "# documentation"]


def _exists_any(repo_path: Path, names: List[str]) -> bool:
    return any((repo_path / name).exists() for name in names)


def _readme_has_docs_section(repo_path: Path) -> bool:
    readme = repo_path / "README.md"
    if not readme.exists():
        return False
    content = readme.read_text(encoding="utf-8", errors="ignore").lower()
    return any(marker in content for marker in DOCS_SECTION_MARKERS)


def run(repo_path: Path, config: Config) -> List[Check]:
    checks: List[Check] = []

    checks.append(
        Check(
            id="structure.readme",
            category="structure",
            severity="warning",
            passed=(repo_path / "README.md").exists(),
            message="README.md present",
        )
    )

    checks.append(
        Check(
            id="structure.license",
            category="structure",
            severity="warning",
            passed=_exists_any(repo_path, ["LICENSE", "LICENSE.md", "LICENSE.txt"]),
            message="LICENSE present",
        )
    )

    checks.append(
        Check(
            id="structure.gitignore",
            category="structure",
            severity="warning",
            passed=(repo_path / ".gitignore").exists(),
            message=".gitignore present",
        )
    )

    checks.append(
        Check(
            id="structure.dependency_manifest",
            category="structure",
            severity="warning",
            passed=_exists_any(repo_path, DEPENDENCY_MANIFESTS),
            message="Dependency manifest present (requirements.txt, pyproject.toml or package.json)",
        )
    )

    checks.append(
        Check(
            id="structure.lockfile",
            category="structure",
            severity="warning",
            passed=_exists_any(repo_path, LOCKFILES),
            message="Lockfile present",
        )
    )

    checks.append(
        Check(
            id="structure.tests_dir",
            category="structure",
            severity="warning",
            passed=_exists_any(repo_path, TEST_DIRS),
            message="Test directory present",
        )
    )

    checks.append(
        Check(
            id="structure.scripts",
            category="structure",
            severity="warning",
            passed=_exists_any(repo_path, SCRIPT_EQUIVALENTS),
            message="Makefile or equivalent scripts present",
        )
    )

    checks.append(
        Check(
            id="structure.docs",
            category="structure",
            severity="warning",
            passed=_exists_any(repo_path, DOCS_DIRS) or _readme_has_docs_section(repo_path),
            message="Docs directory or documentation section present",
        )
    )

    return [c for c in checks if not config.is_check_excepted(c.id)]
