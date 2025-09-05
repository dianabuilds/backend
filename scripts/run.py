from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> None:
    """Run the FastAPI app with uvicorn in development mode."""
    project_root = Path(__file__).resolve().parent.parent
    backend_dir = project_root / "apps" / "backend"
    cmd = [
        "uvicorn",
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    subprocess.run(cmd, cwd=backend_dir, check=True)


if __name__ == "__main__":
    main()
