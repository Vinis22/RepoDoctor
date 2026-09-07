# RepoDoctor

A local CLI that audits a repository's **structure**, **quality** and **security**, and gives it
a score from 0 to 100. Everything runs on your machine, against your filesystem and local `git` —
no external API, no GitHub API, no network calls.

## Documentation

This README is the full documentation. See the sections below for checks, configuration, output
formats and the optional dashboard.

## Why

Every repo accumulates the same kind of drift: no `LICENSE`, no tests folder, a `.env` that
sneaked into git, a password hardcoded in `docker-compose.yml`. RepoDoctor catches this in one
command, locally, before it becomes someone else's problem.

## Install

```bash
make install
```

This creates a virtualenv and installs the `repocheckup` CLI in editable mode plus test
dependencies.

## Usage

```bash
repocheckup .
```

Audits the given path (defaults to `.`), prints a report to the terminal, and writes
`repocheckup.md` and `repocheckup.json` into the audited repository.

```
repocheckup [path] [--output-dir DIR] [--no-md] [--no-json] [--no-color]
```

- `--output-dir DIR` — write the reports somewhere other than the audited repo.
- `--no-md` / `--no-json` — skip writing that report format.
- `--no-color` — disable ANSI colors in the terminal output (useful in CI logs).

**Exit code is `1` if any critical check fails, `0` otherwise** — wire it into a pre-push hook or
CI step directly.

## What it checks

### Structure
- `README.md`
- `LICENSE`
- `.gitignore`
- a dependency manifest (`requirements.txt`, `pyproject.toml` or `package.json`)
- a lockfile (`poetry.lock`, `Pipfile.lock`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `uv.lock`)
- a tests directory (`tests/`, `test/`, `spec/`, `__tests__/`)
- a `Makefile` or equivalent scripts (`scripts/`, `tasks.py`, `noxfile.py`)
- a `docs/` directory or a documentation section in the README

### Quality
- a configured test command (`Makefile` `test:` target, `package.json` `scripts.test`, pytest config)
- a lint/format configuration (`.flake8`, `.eslintrc`, `[tool.ruff]`, `.prettierrc`, etc.)
- a local CI configuration (`.github/workflows`, `.gitlab-ci.yml`, `.circleci/config.yml`, ...)
- recent commits (configurable threshold, default 90 days) — skipped if the path isn't a git repo
- oversized files (configurable threshold, default 5 MB)

### Security
- if `.env` exists, it must be listed in `.gitignore`
- `.env` must not be tracked by git
- sensitive files must not be tracked by git: `.pem`, `id_rsa`, `credentials.json`, `secrets.yml`, `.p12`
- possible secrets in monitored files: `password`, `secret`, `api_key`, `token`, and connection
  strings with embedded credentials (scheme, user, colon, secret, `@`, host) — placeholder values
  (`${VAR}`, `changeme`, `os.environ`, empty strings, ...) are not flagged
- hardcoded passwords in `docker-compose.yml` / `docker-compose.yaml`

Git-dependent checks (tracked files, recent commits) are skipped — not failed — when the target
path is not a git repository.

## Scoring

Starts at 100.

| Severity | Penalty per failed check |
|----------|--------------------------|
| Critical (all security checks) | -20 |
| Warning (structure and quality checks) | -5 |

Score is clamped to `[0, 100]`. A skipped check (e.g. no git repo) never affects the score.

## Configuration — `.repocheckup.yml`

Drop a `.repocheckup.yml` in the audited repo's root to customize the run. See
[`.repocheckup.example.yml`](.repocheckup.example.yml):

```yaml
ignore_paths:
  - vendor
  - fixtures

exceptions:
  - check: quality.large_files
    path: assets/demo_video.mp4   # exempt one specific file from one check
  - check: structure.license      # exempt an entire check for this repo

max_file_size_mb: 10
recent_commit_days: 120
```

- `ignore_paths` — extra paths excluded from file-scanning checks (large files, secret scanning),
  on top of the built-in defaults (`.git`, `node_modules`, `__pycache__`, `.venv`, `dist`, `build`, ...).
- `exceptions` — silence a specific check (`check` only) or a specific path within a check
  (`check` + `path`).
- `max_file_size_mb` — threshold for the large-files check (default `5`).
- `recent_commit_days` — threshold for the recent-commits check (default `90`).

## Output

1. **Terminal** — colored pass/fail report with the final score, printed on every run.
2. **`repocheckup.md`** — the same report as Markdown, good for pasting into a PR description.
3. **`repocheckup.json`** — the same data as structured JSON, good for CI parsing or feeding the
   dashboard below.

## Dashboard (optional, minimal front-end)

A tiny FastAPI page renders the latest `repocheckup.json` — nothing more than the CLI output made
visual, no separate logic:

```bash
REPORT_PATH=repocheckup.json AUDIT_PATH=. uvicorn repodoctor.web.app:app --reload
```

Then open http://localhost:8000. The page has a **"Run audit" button** that triggers a real
`audit(AUDIT_PATH)` run from the browser, writes `repocheckup.json`/`.md` next to `REPORT_PATH`,
and reloads with the result — no need to switch to a terminal for a re-check. The CLI (`repocheckup`)
remains the way to run audits in scripts, pre-commit hooks or CI, where a button doesn't apply.

## Docker

```bash
make up      # builds and starts the dashboard at http://localhost:8000, logs stay attached
make cli     # one-off: audits /workspace and prints/writes the report, no dashboard
make build   # rebuild images without starting anything
make down    # stop everything
make logs    # tail the dashboard logs (only needed if it's running detached elsewhere)
```

These wrap `docker compose` directly (`up --build web`, `run --rm cli .`, `build`, `down`,
`logs -f web`) — nothing hidden, just fewer commands to remember. Both services mount the current
directory into `/workspace`. You don't need `make cli` before `make up`: opening the dashboard and
clicking **"Run audit"** audits `/workspace` directly from the browser. `make cli` is still there
for scripting, CI, or when you just want the terminal/`repocheckup.json` output without opening
the dashboard.

## Demo

```bash
make demo
```

Generates a deliberately messy repo at `examples/demo_repo` (tracked `.env`, a tracked `id_rsa`,
a hardcoded password in `docker-compose.yml`, an oversized file, no README/LICENSE/tests) and
runs `repocheckup` against it, so you can see every check fail and pass in one shot.

## Tests

```bash
make test
```

Runs the pytest suite (`tests/`), which covers every check module, scoring rules, config loading
and the CLI end to end (including real exit codes against real temporary repos).
