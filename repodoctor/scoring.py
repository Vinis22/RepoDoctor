from typing import List

from repodoctor.models import Check

CRITICAL_PENALTY = 20
WARNING_PENALTY = 5


def compute_score(checks: List[Check]) -> int:
    score = 100
    for check in checks:
        if check.passed or check.skipped:
            continue
        score -= CRITICAL_PENALTY if check.severity == "critical" else WARNING_PENALTY
    return max(0, min(100, score))


def has_critical_failure(checks: List[Check]) -> bool:
    return any(
        (not check.passed) and (not check.skipped) and check.severity == "critical"
        for check in checks
    )
