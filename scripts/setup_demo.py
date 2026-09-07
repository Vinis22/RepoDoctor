import shutil
import subprocess
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parent.parent / "examples" / "demo_repo"


def _git(args, cwd, env=None):
    subprocess.run(["git"] + args, cwd=cwd, check=True, env=env, capture_output=True)


def build_demo_repo() -> Path:
    if DEMO_ROOT.exists():
        shutil.rmtree(DEMO_ROOT)
    DEMO_ROOT.mkdir(parents=True)

    (DEMO_ROOT / ".env").write_text("SECRET_KEY=supersecret123\nDB_PASSWORD=hunter2\n", encoding="utf-8")

    (DEMO_ROOT / "id_rsa").write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nfake\n-----END OPENSSH PRIVATE KEY-----\n", encoding="utf-8")

    (DEMO_ROOT / "config.py").write_text(
        'API_KEY = "sk-live-abcdef1234567890"\n'
        'password = "letmein123"\n',
        encoding="utf-8",
    )

    (DEMO_ROOT / "docker-compose.yml").write_text(
        "services:\n"
        "  db:\n"
        "    image: postgres\n"
        "    environment:\n"
        "      POSTGRES_PASSWORD: hardcoded_password_123\n",
        encoding="utf-8",
    )

    (DEMO_ROOT / "app.py").write_text("print('hello from the messy demo repo')\n", encoding="utf-8")

    large_file = DEMO_ROOT / "assets" / "big_binary.dat"
    large_file.parent.mkdir(parents=True, exist_ok=True)
    large_file.write_bytes(b"0" * (6 * 1024 * 1024))

    _git(["init", "-q"], cwd=DEMO_ROOT)
    _git(["config", "user.email", "demo@repodoctor.local"], cwd=DEMO_ROOT)
    _git(["config", "user.name", "RepoDoctor Demo"], cwd=DEMO_ROOT)
    _git(["add", "."], cwd=DEMO_ROOT)
    _git(["commit", "-q", "-m", "initial messy commit"], cwd=DEMO_ROOT)

    return DEMO_ROOT


if __name__ == "__main__":
    path = build_demo_repo()
    print(f"Demo repo created at {path}")
