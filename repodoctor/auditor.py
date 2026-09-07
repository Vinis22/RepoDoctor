from pathlib import Path

from repodoctor.checks import quality, security, structure
from repodoctor.config import load_config
from repodoctor.models import Report
from repodoctor.scoring import compute_score, has_critical_failure


def audit(repo_path: Path) -> Report:
    repo_path = repo_path.resolve()
    config = load_config(repo_path)

    checks = []
    checks.extend(structure.run(repo_path, config))
    checks.extend(quality.run(repo_path, config))
    checks.extend(security.run(repo_path, config))

    score = compute_score(checks)
    critical = has_critical_failure(checks)

    return Report(
        repo_path=str(repo_path),
        score=score,
        checks=checks,
        has_critical_failure=critical,
    )
