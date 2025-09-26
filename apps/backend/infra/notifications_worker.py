# Register workers on import
from domains.platform.notifications.workers import *  # noqa: F401,F403
from packages.worker import main as worker_main

if __name__ == "__main__":
    worker_main(["--name", "notifications.broadcast"])
