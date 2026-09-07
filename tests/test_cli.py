import json

from repodoctor.cli import main


def _make_good_repo(tmp_path):
    (tmp_path / "README.md").write_text("# Project\n\n## Documentation\nSee docs.\n")
    (tmp_path / "LICENSE").write_text("MIT")
    (tmp_path / ".gitignore").write_text(".venv/\n")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n[tool.pytest.ini_options]\n")
    (tmp_path / "poetry.lock").write_text("")
    (tmp_path / "tests").mkdir()
    (tmp_path / "Makefile").write_text("test:\n\tpytest\n")
    (tmp_path / ".flake8").write_text("[flake8]\n")


def test_cli_exit_code_zero_for_clean_repo(tmp_path):
    _make_good_repo(tmp_path)
    exit_code = main([str(tmp_path), "--no-color"])
    assert exit_code == 0
    assert (tmp_path / "repocheckup.json").exists()
    assert (tmp_path / "repocheckup.md").exists()


def test_cli_exit_code_one_for_critical_issue(tmp_path):
    (tmp_path / ".env").write_text("KEY=value\n")
    exit_code = main([str(tmp_path), "--no-color"])
    assert exit_code == 1

    data = json.loads((tmp_path / "repocheckup.json").read_text())
    assert data["has_critical_failure"] is True


def test_cli_output_dir_option(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    output = tmp_path / "out"
    main([str(repo), "--output-dir", str(output), "--no-color"])
    assert (output / "repocheckup.json").exists()


def test_cli_no_md_and_no_json_flags(tmp_path):
    main([str(tmp_path), "--no-md", "--no-json", "--no-color"])
    assert not (tmp_path / "repocheckup.md").exists()
    assert not (tmp_path / "repocheckup.json").exists()


def test_cli_nonexistent_path_returns_error(tmp_path):
    exit_code = main([str(tmp_path / "missing"), "--no-color"])
    assert exit_code == 2
