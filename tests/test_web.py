import json
import os

from fastapi.testclient import TestClient


def _client(tmp_path, report=None, audit_path=None):
    report_path = tmp_path / "repocheckup.json"
    if report is not None:
        report_path.write_text(json.dumps(report), encoding="utf-8")
    os.environ["REPORT_PATH"] = str(report_path)
    os.environ["AUDIT_PATH"] = str(audit_path or tmp_path)

    from repodoctor.web import app as app_module
    import importlib
    importlib.reload(app_module)

    return TestClient(app_module.app)


def _sample_report():
    return {
        "repo_path": "/tmp/repo",
        "score": 42,
        "has_critical_failure": True,
        "checks": [
            {
                "id": "security.env_tracked",
                "category": "security",
                "severity": "critical",
                "passed": False,
                "skipped": False,
                "message": ".env is tracked by git",
                "details": [],
            }
        ],
    }


def test_index_without_report_shows_empty_state(tmp_path):
    client = _client(tmp_path, report=None)
    response = client.get("/")
    assert response.status_code == 200
    assert "No report found" in response.text


def test_index_with_report_renders_score_and_checks(tmp_path):
    client = _client(tmp_path, report=_sample_report())
    response = client.get("/")
    assert response.status_code == 200
    assert "42" in response.text
    assert ".env is tracked by git" in response.text


def test_api_report_returns_json(tmp_path):
    client = _client(tmp_path, report=_sample_report())
    response = client.get("/api/report")
    assert response.status_code == 200
    assert response.json()["score"] == 42


def test_api_report_404_without_report(tmp_path):
    client = _client(tmp_path, report=None)
    response = client.get("/api/report")
    assert response.status_code == 404


def test_run_audit_writes_report_and_redirects(tmp_path):
    audit_target = tmp_path / "target"
    audit_target.mkdir()
    (audit_target / ".env").write_text("KEY=value\n")

    client = _client(tmp_path, report=None, audit_path=audit_target)
    response = client.post("/run", follow_redirects=False)

    assert response.status_code == 303
    report_path = tmp_path / "repocheckup.json"
    assert report_path.exists()

    data = json.loads(report_path.read_text())
    assert data["has_critical_failure"] is True
    assert (tmp_path / "repocheckup.md").exists()


def test_index_shows_run_audit_button(tmp_path):
    client = _client(tmp_path, report=None)
    response = client.get("/")
    assert "Run audit" in response.text
