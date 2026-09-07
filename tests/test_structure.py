from repodoctor.checks import structure
from repodoctor.config import Config, Exception_


def _find(checks, check_id):
    return next(c for c in checks if c.id == check_id)


def test_empty_repo_fails_all_structure_checks(tmp_path):
    checks = structure.run(tmp_path, Config())
    assert all(not c.passed for c in checks)


def test_complete_repo_passes_all_structure_checks(tmp_path):
    (tmp_path / "README.md").write_text("# Project\n\n## Documentation\nSee docs.\n")
    (tmp_path / "LICENSE").write_text("MIT")
    (tmp_path / ".gitignore").write_text(".venv/\n")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    (tmp_path / "poetry.lock").write_text("")
    (tmp_path / "tests").mkdir()
    (tmp_path / "Makefile").write_text("test:\n\techo test\n")

    checks = structure.run(tmp_path, Config())
    assert all(c.passed for c in checks)


def test_exception_skips_check(tmp_path):
    config = Config(exceptions=[Exception_(check="structure.license")])
    checks = structure.run(tmp_path, config)
    assert _find(checks, "structure.readme") is not None
    assert not any(c.id == "structure.license" for c in checks)
