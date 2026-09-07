from repodoctor.config import load_config


def test_load_config_defaults_when_missing(tmp_path):
    config = load_config(tmp_path)
    assert config.max_file_size_mb == 5.0
    assert config.recent_commit_days == 90
    assert config.exceptions == []


def test_load_config_reads_yaml(tmp_path):
    (tmp_path / ".repocheckup.yml").write_text(
        "ignore_paths:\n"
        "  - vendor\n"
        "exceptions:\n"
        "  - check: structure.license\n"
        "max_file_size_mb: 10\n"
        "recent_commit_days: 30\n"
    )
    config = load_config(tmp_path)
    assert "vendor" in config.ignore_paths
    assert config.max_file_size_mb == 10
    assert config.recent_commit_days == 30
    assert config.is_check_excepted("structure.license")


def test_is_ignored_matches_prefix(tmp_path):
    config = load_config(tmp_path)
    assert config.is_ignored("node_modules/some/file.js")
    assert not config.is_ignored("app/some/file.py")
