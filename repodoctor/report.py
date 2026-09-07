from datetime import datetime, timezone
from typing import Dict, List

from repodoctor.models import Check, Report

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
GRAY = "\033[90m"

CATEGORY_ORDER = ["structure", "quality", "security"]
CATEGORY_LABELS = {"structure": "Structure", "quality": "Quality", "security": "Security"}


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


def _group_by_category(checks: List[Check]) -> Dict[str, List[Check]]:
    grouped: Dict[str, List[Check]] = {category: [] for category in CATEGORY_ORDER}
    for check in checks:
        grouped.setdefault(check.category, []).append(check)
    return grouped


def render_terminal(report: Report, use_color: bool = True) -> str:
    lines = []
    grouped = _group_by_category(report.checks)

    def c(code: str, text: str) -> str:
        return f"{code}{text}{RESET}" if use_color else text

    lines.append(c(BOLD, f"RepoDoctor report - {report.repo_path}"))
    lines.append("")

    for category in CATEGORY_ORDER:
        checks = grouped.get(category, [])
        if not checks:
            continue
        lines.append(c(BOLD, CATEGORY_LABELS.get(category, category.title())))
        for check in checks:
            if check.skipped:
                symbol, color = "-", GRAY
            elif check.passed:
                symbol, color = "OK", GREEN
            else:
                symbol, color = ("CRIT" if check.severity == "critical" else "WARN"), (
                    RED if check.severity == "critical" else YELLOW
                )
            lines.append(f"  {c(color, f'[{symbol}]')} {check.message}")
            for detail in check.details[:5]:
                lines.append(c(GRAY, f"        - {detail}"))
            if len(check.details) > 5:
                lines.append(c(GRAY, f"        ... and {len(check.details) - 5} more"))
        lines.append("")

    grade = _grade(report.score)
    score_color = GREEN if report.score >= 75 else (YELLOW if report.score >= 40 else RED)
    lines.append(c(BOLD, f"Score: ") + c(score_color, f"{report.score}/100 ({grade})"))
    if report.has_critical_failure:
        lines.append(c(RED, "Critical issues found."))

    return "\n".join(lines)


def render_markdown(report: Report) -> str:
    grouped = _group_by_category(report.checks)
    grade = _grade(report.score)
    lines = [
        f"# RepoDoctor report",
        "",
        f"**Repository:** `{report.repo_path}`  ",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}  ",
        f"**Score:** {report.score}/100 ({grade})",
        "",
    ]

    for category in CATEGORY_ORDER:
        checks = grouped.get(category, [])
        if not checks:
            continue
        lines.append(f"## {CATEGORY_LABELS.get(category, category.title())}")
        lines.append("")
        for check in checks:
            if check.skipped:
                symbol = "⏭️"
            elif check.passed:
                symbol = "✅"
            else:
                symbol = "🛑" if check.severity == "critical" else "⚠️"
            lines.append(f"- {symbol} {check.message}")
            for detail in check.details:
                lines.append(f"  - `{detail}`")
        lines.append("")

    if report.has_critical_failure:
        lines.append("> **Critical issues found.**")
        lines.append("")

    return "\n".join(lines)


def to_dict(report: Report) -> dict:
    return {
        "repo_path": report.repo_path,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "score": report.score,
        "has_critical_failure": report.has_critical_failure,
        "checks": [
            {
                "id": check.id,
                "category": check.category,
                "severity": check.severity,
                "passed": check.passed,
                "skipped": check.skipped,
                "message": check.message,
                "details": check.details,
            }
            for check in report.checks
        ],
    }
