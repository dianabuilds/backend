from __future__ import annotations

import datetime as dt
import os
import shlex
import shutil

# Bandit: subprocess usage is limited to predefined command lists.
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Sequence, TypedDict


class CheckSpec(TypedDict):
    title: str
    command: Sequence[str]
    cwd: Path


class CheckResult(TypedDict):
    title: str
    command: str
    returncode: int | None
    output: str
    success: bool


PROJECT_BANDIT_PATHS = [
    "apps/backend/app",
    "apps/backend/domains",
    "apps/backend/packages",
    "apps/backend/workers",
    "scripts",
    "health",
]

PROJECT_VULTURE_PATHS = [
    "apps/backend/app",
    "apps/backend/domains",
    "apps/backend/packages",
    "apps/backend/workers",
    "apps/backend/scripts",
    "health",
    "scripts",
]

BANDIT_BASE_EXCLUDES = [
    "apps/backend/.venv",
    "tests",
    "apps/backend/app/tests",
    "apps/backend/domains/product/_template",
]
VULTURE_EXCLUDES = "apps/backend/.venv"


def _format_command(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _build_checks(repo_root: Path) -> list[CheckSpec]:
    app_root = repo_root / "apps" / "backend"
    var_dir = repo_root / "var"
    sbom_path = var_dir / "sbom.json"

    requirements_file = repo_root / "apps" / "backend" / "requirements.txt"

    backend_root = repo_root / "apps" / "backend"
    test_dirs: list[str] = []
    for path in backend_root.rglob("tests"):
        if not path.is_dir():
            continue
        relative_parts = path.relative_to(repo_root).parts
        if any(part.startswith(".") for part in relative_parts):
            continue
        test_dirs.append(str(Path(*relative_parts)).replace("\\", "/"))
    bandit_excludes = BANDIT_BASE_EXCLUDES + test_dirs
    bandit_excludes.append(
        "apps/backend/domains/platform/notifications/adapters/sql/broadcasts.py"
    )
    bandit_excludes.append("apps/backend/domains/platform/search/adapters/sql/index.py")
    bandit_excludes.append(
        "apps/backend/domains/product/achievements/adapters/sql/repository.py"
    )
    bandit_excludes.append(
        "apps/backend/domains/product/navigation/infrastructure/relations.py"
    )
    bandit_excludes.append(
        "apps/backend/domains/product/navigation/application/service.py"
    )

    cyclonedx_args = [
        "requirements",
        str(requirements_file),
        "--of",
        "JSON",
        "-o",
        str(sbom_path),
    ]
    cyclonedx_exe = shutil.which("cyclonedx-py")
    if cyclonedx_exe:
        cyclonedx_cmd = [cyclonedx_exe, *cyclonedx_args]
    else:
        cyclonedx_cmd = [sys.executable, "-m", "cyclonedx_py", *cyclonedx_args]

    health_exe = shutil.which("health")
    if health_exe:
        health_cmd = [health_exe, "bench"]
    else:
        health_cmd = [sys.executable, "-m", "health", "bench"]

    return [
        {
            "title": "Ruff",
            "command": [
                sys.executable,
                "-m",
                "ruff",
                "check",
                ".",
                "--config",
                "pyproject.toml",
            ],
            "cwd": app_root,
        },
        {
            "title": "Mypy",
            "command": [
                sys.executable,
                "-m",
                "mypy",
                "--config-file",
                str(repo_root / "mypy.ini"),
                "apps/backend",
            ],
            "cwd": repo_root,
        },
        {
            "title": "Bandit",
            "command": [
                sys.executable,
                "-m",
                "bandit",
                "-q",
                "-r",
                *PROJECT_BANDIT_PATHS,
                "--skip",
                "B608",
                "-x",
                ",".join(bandit_excludes),
            ],
            "cwd": repo_root,
        },
        {
            "title": "Vulture",
            "command": [
                sys.executable,
                "-m",
                "vulture",
                *PROJECT_VULTURE_PATHS,
                "--min-confidence",
                "80",
                "--exclude",
                VULTURE_EXCLUDES,
            ],
            "cwd": repo_root,
        },
        {
            "title": "pip-audit",
            "command": [
                sys.executable,
                "-m",
                "pip_audit",
                "--requirement",
                str(requirements_file),
                "--requirement",
                str(repo_root / "tests" / "requirements-test.txt"),
            ],
            "cwd": repo_root,
        },
        {
            "title": "CycloneDX",
            "command": cyclonedx_cmd,
            "cwd": repo_root,
        },
        {
            "title": "Health Bench",
            "command": health_cmd,
            "cwd": repo_root,
        },
    ]


def _run_check(title: str, command: Sequence[str], cwd: Path) -> CheckResult:
    display_cmd = _format_command(command)
    print(f"[validate_repo] {title}: {display_cmd}")
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        # Bandit: commands originate from a static allowlist.
        completed = subprocess.run(  # nosec B603
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=env,
        )
    except FileNotFoundError as exc:
        message = f"Command not found: {exc.filename}"
        print(f"[validate_repo] {title}: missing executable")
        return {
            "title": title,
            "command": display_cmd,
            "returncode": None,
            "output": message,
            "success": False,
        }

    output_text = (completed.stdout or "") + (completed.stderr or "")
    success = completed.returncode == 0
    status = "OK" if success else f"FAIL ({completed.returncode})"
    print(f"[validate_repo] {title}: {status}")
    return {
        "title": title,
        "command": display_cmd,
        "returncode": completed.returncode,
        "output": output_text.strip(),
        "success": success,
    }


def _write_report(results: Sequence[CheckResult], report_path: Path) -> None:
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M:%SZ")
    lines: list[str] = ["# Repository Validation Report", f"Generated: {timestamp}"]

    for result in results:
        title = result["title"]
        command = result["command"]
        returncode = result["returncode"]
        output = result["output"] or "(no output)"
        status = "success" if result["success"] else "failure"

        lines.append("")
        lines.append(f"## {title}")
        lines.append(f"Command: `{command}`")
        if returncode is None:
            lines.append("Exit Code: not executed")
        else:
            lines.append(f"Exit Code: {returncode}")
        lines.append(f"Result: {status}")
        lines.append("")
        lines.append("```text")
        payload = output.splitlines() or ["(no output)"]
        lines.extend(payload)
        lines.append("```")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    checks = _build_checks(repo_root)
    results: list[CheckResult] = []

    for entry in checks:
        result = _run_check(entry["title"], entry["command"], entry["cwd"])
        results.append(result)

    report_path = repo_root / "reports" / "validate_repo.md"
    _write_report(results, report_path)

    all_success = all(result["success"] for result in results)
    if all_success:
        print(f"[validate_repo] Report written to {report_path}")
        return 0

    print(f"[validate_repo] Report written to {report_path}; failures detected")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
