from repodoctor.checks import quality
from repodoctor.config import Config
from tests.conftest import commit_all, init_git_repo


def _find(checks, check_id):
    return next(c for c in checks if c.id == check_id)


def test_test_command_detected_in_makefile(tmp_path):
    (tmp_path / "Makefile").write_text("test:\n\tpytest\n")
    checks = quality.run(tmp_path, Config())
    assert _find(checks, "quality.test_command").passed


def test_lint_config_detected(tmp_path):
    (tmp_path / ".flake8").write_text("[flake8]\n")
    checks = quality.run(tmp_path, Config())
    assert _find(checks, "quality.lint_config").passed


def test_ci_config_detected(tmp_path):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n")
    checks = quality.run(tmp_path, Config())
    assert _find(checks, "quality.ci_config").passed


def test_large_file_detected(tmp_path):
    big = tmp_path / "big.bin"
    big.write_bytes(b"0" * (6 * 1024 * 1024))
    checks = quality.run(tmp_path, Config(max_file_size_mb=5))
    check = _find(checks, "quality.large_files")
    assert not check.passed
    assert "big.bin" in check.details


def test_recent_commit_passes_for_fresh_commit(tmp_path):
    init_git_repo(tmp_path)
    (tmp_path / "file.txt").write_text("content")
    commit_all(tmp_path)
    checks = quality.run(tmp_path, Config())
    assert _find(checks, "quality.recent_commits").passed


def test_recent_commit_skipped_without_git(tmp_path):
    checks = quality.run(tmp_path, Config())
    check = _find(checks, "quality.recent_commits")
    assert check.skipped
