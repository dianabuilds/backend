from __future__ import annotations

import logging
import os
import sys

from . import get_worker_container


def run(*, topics: str | None = None) -> None:
    """Start the events relay loop."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
        )

    container = get_worker_container()
    topic_source = (
        topics or os.getenv("APP_EVENT_TOPICS") or str(container.settings.event_topics)
    )
    logging.getLogger("events.worker").info(
        "Starting events worker; topics=%s", topic_source
    )
    try:
        container.events.run(block_ms=5000, count=100)
    except KeyboardInterrupt:
        print("\nEvents worker stopped.")
        sys.exit(0)


def main() -> None:  # pragma: no cover - runtime script
    run()


if __name__ == "__main__":  # pragma: no cover
    main()
