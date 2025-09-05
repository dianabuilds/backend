from __future__ import annotations

import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = REPO_ROOT / "reports" / "validate_repo.md"


def run_command(name: str, cmd: list[str]) -> dict[str, object]:
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
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
        ("ruff", ["ruff", "check", "."]),
        ("mypy", ["mypy", "apps/backend"]),
        ("bandit", ["bandit", "-r", "apps/backend", "-ll"]),
        ("vulture", ["vulture", "apps/backend"]),
        ("pip-audit", ["pip-audit", "-r", "requirements.txt"]),
        ("cyclonedx-bom", ["cyclonedx-bom", "-o", "sbom.json"]),
    ]
    results = []
    had_error = False
    for name, cmd in steps:
        res = run_command(name, cmd)
        results.append(res)
        if res["code"] != 0:
            had_error = True
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
