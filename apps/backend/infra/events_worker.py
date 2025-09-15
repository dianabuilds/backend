from __future__ import annotations

import logging
import os
import sys

from app.api_gateway.wires import build_container


def main() -> None:  # pragma: no cover - runtime script
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    container = build_container()
    topics = os.getenv("APP_EVENT_TOPICS", str(container.settings.event_topics))
    logging.getLogger("events.worker").info("Starting events worker; topics=%s", topics)
    try:
        container.events.run(block_ms=5000, count=100)
    except KeyboardInterrupt:
        print("\nEvents worker stopped.")
        sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
