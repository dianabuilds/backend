from __future__ import annotations

import os
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = REPO_ROOT / "reports" / "validate_repo.md"


def run_command(name: str, cmd: list[str], *, cwd: Path | None = None) -> dict[str, object]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
        )
        output = (result.stdout + result.stderr).strip()
        code = result.returncode
    except FileNotFoundError as exc:  # command not found
        output = str(exc)
        code = 1
    return {"name": name, "cmd": " ".join(cmd), "output": output, "code": code}


def run_health_bench(url: str, count: int) -> dict[str, object]:
    durations: list[float] = []
    errors: list[str] = []
    success = 0
    for _ in range(count):
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                resp.read()
                if resp.status == 200:
                    success += 1
                else:
                    errors.append(f"status {resp.status}")
        except urllib.error.URLError as exc:  # server unreachable
            errors.append(str(exc))
        durations.append(time.perf_counter() - start)
    avg = statistics.mean(durations) if durations else 0.0
    output_lines = [f"success: {success}/{count}", f"avg_time_ms: {avg*1000:.2f}"]
    if errors:
        output_lines.append("errors:")
        output_lines.extend(errors)
    return {
        "name": "health_bench",
        "cmd": f"GET {url} x{count}",
        "output": "\n".join(output_lines),
        "code": 0 if not errors else 1,
    }


def main() -> int:
    steps = [
        {"name": "ruff", "cmd": ["ruff", "check", "."]},
        {"name": "mypy", "cmd": ["mypy", "apps/backend"]},
        # Run import-linter from the package root so it can resolve 'app'.
        {
            "name": "import-linter",
            "cmd": ["lint-imports", "--config", "../../importlinter.ini"],
            "cwd": REPO_ROOT / "apps/backend",
        },
        {"name": "bandit", "cmd": ["bandit", "-r", "apps/backend", "-ll"]},
        {"name": "vulture", "cmd": ["vulture", "apps/backend"]},
        {"name": "pip-audit", "cmd": ["pip-audit", "-r", "requirements.txt"]},
        {"name": "cyclonedx-bom", "cmd": ["cyclonedx-bom", "-o", "sbom.json"]},
    ]
    results = []
    had_error = False
    for step in steps:
        name = step["name"]
        cmd = step["cmd"]
        cwd = step.get("cwd")
        res = run_command(name, cmd, cwd=cwd)
        results.append(res)
        if res["code"] != 0:
            had_error = True
    skip_bench = os.getenv("VALIDATE_SKIP_BENCH", "").lower() in {"1", "true", "yes"}
    if not skip_bench:
        bench = run_health_bench("http://localhost:8000/health", 10)
        results.append(bench)
        if bench["code"] != 0:
            had_error = True

    REPORT_PATH.parent.mkdir(exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("# Repository Validation Report\n\n")
        for r in results:
            f.write(f"## {r['name']}\n\n")
            f.write(f"Command: `{r['cmd']}`\n\n")
            f.write("```\n")
            f.write(r["output"])
            f.write("\n```\n\n")

    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
