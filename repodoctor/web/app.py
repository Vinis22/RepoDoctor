import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from repodoctor.auditor import audit
from repodoctor.report import render_markdown, to_dict

BASE_DIR = Path(__file__).resolve().parent
REPORT_PATH = Path(os.environ.get("REPORT_PATH", "repocheckup.json"))
AUDIT_PATH = Path(os.environ.get("AUDIT_PATH", "."))

app = FastAPI(title="RepoDoctor")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

CATEGORY_LABELS = {"structure": "Structure", "quality": "Quality", "security": "Security"}


def _load_report():
    if not REPORT_PATH.exists():
        return None
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _grouped_checks(report: dict):
    grouped = {key: [] for key in CATEGORY_LABELS}
    for check in report["checks"]:
        grouped.setdefault(check["category"], []).append(check)
    return [
        {"key": key, "label": CATEGORY_LABELS.get(key, key.title()), "checks": grouped[key]}
        for key in grouped
        if grouped[key]
    ]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    report = _load_report()
    if report is None:
        return templates.TemplateResponse(
            request,
            "index.html",
            {"report": None, "report_path": str(REPORT_PATH)},
        )

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "report": report,
            "grade": _grade(report["score"]),
            "groups": _grouped_checks(report),
            "report_path": str(REPORT_PATH),
        },
    )


@app.post("/run")
async def run_audit():
    report = audit(AUDIT_PATH)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(to_dict(report), indent=2), encoding="utf-8")
    (REPORT_PATH.parent / "repocheckup.md").write_text(render_markdown(report), encoding="utf-8")
    return RedirectResponse(url="/", status_code=303)


@app.get("/api/report")
async def api_report():
    report = _load_report()
    if report is None:
        return JSONResponse(status_code=404, content={"detail": "no report found"})
    return report


@app.get("/health")
async def health():
    return {"status": "ok"}
