from repodoctor.models import Check
from repodoctor.scoring import compute_score, has_critical_failure


def _check(passed, severity="warning", skipped=False):
    return Check(id="x", category="structure", severity=severity, passed=passed, message="", skipped=skipped)


def test_perfect_score():
    checks = [_check(True), _check(True, severity="critical")]
    assert compute_score(checks) == 100
    assert not has_critical_failure(checks)


def test_critical_failure_penalizes_more_than_warning():
    critical_score = compute_score([_check(False, severity="critical")])
    warning_score = compute_score([_check(False, severity="warning")])
    assert critical_score < warning_score


def test_score_never_below_zero():
    checks = [_check(False, severity="critical") for _ in range(10)]
    assert compute_score(checks) == 0


def test_skipped_checks_do_not_penalize():
    checks = [_check(False, severity="critical", skipped=True)]
    assert compute_score(checks) == 100
    assert not has_critical_failure(checks)


def test_has_critical_failure_true_when_unskipped_critical_fails():
    checks = [_check(False, severity="critical")]
    assert has_critical_failure(checks)
