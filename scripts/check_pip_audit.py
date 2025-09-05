from __future__ import annotations

import json
import sys
from pathlib import Path


def main(path: str) -> int:
    data = json.loads(Path(path).read_text())
    critical = []
    for dep in data.get("dependencies", []):
        for vuln in dep.get("vulns", []):
            severity = (vuln.get("severity") or "").upper()
            if severity == "CRITICAL":
                critical.append((dep.get("name"), vuln.get("id")))
    if critical:
        for name, vid in critical:
            print(f"CRITICAL: {name} -> {vid}", file=sys.stderr)
        return 1
    print("No critical vulnerabilities found")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: check_pip_audit.py <report.json>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
