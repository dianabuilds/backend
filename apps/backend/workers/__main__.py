from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

from . import events_worker, notifications_worker, schedule_worker


def _configure_logging(level: str | None) -> None:
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    else:
        root.setLevel(log_level)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backend workers entrypoint")
    subparsers = parser.add_subparsers(dest="worker", required=True)

    events_parser = subparsers.add_parser("events", help="Run the events relay worker")
    events_parser.add_argument(
        "--topics",
        help="Override topics for logging (defaults to APP_EVENT_TOPICS or settings)",
    )
    events_parser.add_argument(
        "--log-level", dest="log_level", help="Logging level", default="INFO"
    )

    scheduler_parser = subparsers.add_parser("scheduler", help="Run the scheduler worker")
    scheduler_parser.add_argument(
        "--interval",
        type=int,
        help="Override tick interval in seconds (defaults to env NODES_SCHEDULER_INTERVAL)",
    )
    scheduler_parser.add_argument(
        "--log-level", dest="log_level", help="Logging level", default="INFO"
    )

    notifications_parser = subparsers.add_parser(
        "notifications",
        help="Run the notifications broadcast worker",
    )
    notifications_parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Additional arguments forwarded to packages.worker runner",
    )
    notifications_parser.add_argument(
        "--log-level", dest="log_level", help="Logging level", default="INFO"
    )

    args = parser.parse_args(argv)

    _configure_logging(getattr(args, "log_level", None))

    if args.worker == "events":
        events_worker.run(topics=args.topics)
    elif args.worker == "scheduler":
        schedule_worker.run(interval=args.interval)
    elif args.worker == "notifications":
        extra = getattr(args, "extra", None) or []
        notifications_worker.run(list(extra))
    else:  # pragma: no cover - argparse prevents this
        parser.error(f"Unknown worker: {args.worker}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
