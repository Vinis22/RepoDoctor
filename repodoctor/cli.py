import argparse
import json
import sys
from pathlib import Path

from repodoctor.auditor import audit
from repodoctor.report import render_markdown, render_terminal, to_dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repocheckup",
        description="Audit a repository's structure, quality and security, fully locally.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Path to the repository to audit")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write repocheckup.md and repocheckup.json (default: the audited repo)",
    )
    parser.add_argument("--no-md", action="store_true", help="Do not write repocheckup.md")
    parser.add_argument("--no-json", action="store_true", help="Do not write repocheckup.json")
    parser.add_argument("--no-color", action="store_true", help="Disable colored terminal output")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_path = Path(args.path)
    if not repo_path.exists():
        print(f"error: path does not exist: {repo_path}", file=sys.stderr)
        return 2

    report = audit(repo_path)

    print(render_terminal(report, use_color=not args.no_color))

    output_dir = Path(args.output_dir) if args.output_dir else Path(report.repo_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_md:
        (output_dir / "repocheckup.md").write_text(render_markdown(report), encoding="utf-8")

    if not args.no_json:
        (output_dir / "repocheckup.json").write_text(
            json.dumps(to_dict(report), indent=2), encoding="utf-8"
        )

    return 1 if report.has_critical_failure else 0


if __name__ == "__main__":
    sys.exit(main())
