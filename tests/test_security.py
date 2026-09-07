from repodoctor.checks import security
from repodoctor.config import Config
from tests.conftest import commit_all, init_git_repo


def _find(checks, check_id):
    return next(c for c in checks if c.id == check_id)


def test_env_not_present_passes(tmp_path):
    checks = security.run(tmp_path, Config())
    assert _find(checks, "security.env_gitignored").passed


def test_env_present_not_gitignored_fails(tmp_path):
    (tmp_path / ".env").write_text("KEY=value\n")
    checks = security.run(tmp_path, Config())
    assert not _find(checks, "security.env_gitignored").passed


def test_env_present_and_gitignored_passes(tmp_path):
    (tmp_path / ".env").write_text("KEY=value\n")
    (tmp_path / ".gitignore").write_text(".env\n")
    checks = security.run(tmp_path, Config())
    assert _find(checks, "security.env_gitignored").passed


def test_env_tracked_by_git_fails(tmp_path):
    init_git_repo(tmp_path)
    (tmp_path / ".env").write_text("KEY=value\n")
    commit_all(tmp_path)
    checks = security.run(tmp_path, Config())
    assert not _find(checks, "security.env_tracked").passed


def test_sensitive_file_tracked_fails(tmp_path):
    init_git_repo(tmp_path)
    (tmp_path / "id_rsa").write_text("fake key")
    commit_all(tmp_path)
    checks = security.run(tmp_path, Config())
    check = _find(checks, "security.sensitive_files_tracked")
    assert not check.passed
    assert "id_rsa" in check.details


def test_hardcoded_secret_detected(tmp_path):
    (tmp_path / "config.py").write_text('api_key = "sk-live-1234567890"\n')
    checks = security.run(tmp_path, Config())
    assert not _find(checks, "security.secrets_in_files").passed


def test_placeholder_secret_not_flagged(tmp_path):
    (tmp_path / "config.py").write_text('password = "${DB_PASSWORD}"\n')
    checks = security.run(tmp_path, Config())
    assert _find(checks, "security.secrets_in_files").passed


def test_hardcoded_password_in_compose_detected(tmp_path):
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  db:\n    environment:\n      POSTGRES_PASSWORD: supersecret\n"
    )
    checks = security.run(tmp_path, Config())
    assert not _find(checks, "security.compose_passwords").passed


def test_compose_password_from_env_var_not_flagged(tmp_path):
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  db:\n    environment:\n      POSTGRES_PASSWORD: ${DB_PASSWORD}\n"
    )
    checks = security.run(tmp_path, Config())
    assert _find(checks, "security.compose_passwords").passed
