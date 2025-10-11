from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Tuple


@dataclass(frozen=True)
class BenchCheck:
    name: str
    description: str
    func: Callable[[Path], Tuple[bool, str]]


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _check_api_gateway_health(repo_root: Path) -> Tuple[bool, str]:
    main_py = repo_root / "apps" / "backend" / "app" / "api_gateway" / "main.py"
    text = _read_text(main_py)
    if not text:
        return False, "missing apps/backend/app/api_gateway/main.py"
    if '@app.get("/healthz"' in text:
        return True, "found /healthz endpoint"
    return False, "missing /healthz endpoint"


def _check_health_tests(repo_root: Path) -> Tuple[bool, str]:
    test_file = repo_root / "tests" / "integration" / "test_api_gateway_smoke.py"
    text = _read_text(test_file)
    if not text:
        return False, "missing test_api_gateway_smoke.py"
    if "test_health_endpoints" in text:
        return True, "found integration test"
    return False, "integration test not found"


def _check_admin_health(repo_root: Path) -> Tuple[bool, str]:
    admin_file = (
        repo_root
        / "apps"
        / "backend"
        / "domains"
        / "platform"
        / "admin"
        / "api"
        / "endpoints"
        / "health.py"
    )
    text = _read_text(admin_file)
    if not text:
        return False, "missing admin health endpoint"
    if '@router.get("/health")' in text:
        return True, "admin /health endpoint present"
    return False, "admin /health endpoint not found"


def run_bench(repo_root: Path) -> int:
    checks = [
        BenchCheck(
            "api_gateway_health",
            "API Gateway health endpoint",
            _check_api_gateway_health,
        ),
        BenchCheck("integration_tests", "Integration smoke test", _check_health_tests),
        BenchCheck("admin_health", "Admin health endpoint", _check_admin_health),
    ]

    results = []
    for check in checks:
        ok, details = check.func(repo_root)
        results.append((check, ok, details))

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    success_pct = (passed / total * 100.0) if total else 100.0

    print(f"Health bench: {passed}/{total} checks passed ({success_pct:.1f}% success)")
    for check, ok, details in results:
        status = "OK" if ok else "FAIL"
        print(f" - {check.name}: {status} - {details}")

    return 0 if passed == total else 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="health")
    subparsers = parser.add_subparsers(dest="command")

    bench_parser = subparsers.add_parser("bench", help="Run repository health checks")
    bench_parser.set_defaults(command="bench")

    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    if args.command == "bench":
        return run_bench(repo_root)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
