from __future__ import annotations

from domains.platform.telemetry.workers import *  # noqa: F401,F403 - register workers
from packages.worker import main as worker_main


def run(extra_args: list[str] | None = None) -> None:
    args = ["--name", "telemetry.rum_rollup"]
    if extra_args:
        args.extend(extra_args)
    worker_main(args)


def main() -> None:  # pragma: no cover - runtime script
    run()


if __name__ == "__main__":  # pragma: no cover
    main()
