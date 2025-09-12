from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path


TOKENS = {
    "{{DOMAIN}}": lambda name: name.capitalize(),
    "{{domain}}": lambda name: name.lower(),
}


def render_text(content: str, name: str) -> str:
    for k, fn in TOKENS.items():
        content = content.replace(k, fn(name))
    return content


def copy_tree(src: Path, dst: Path, name: str) -> None:
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        # Render directory names with tokens if any
        rel_str = render_text(str(rel), name)
        out_dir = dst / rel_str if rel_str != "." else dst
        out_dir.mkdir(parents=True, exist_ok=True)
        for d in dirs:
            (out_dir / render_text(d, name)).mkdir(parents=True, exist_ok=True)
        for f in files:
            in_path = Path(root) / f
            out_name = render_text(f, name)
            out_path = out_dir / out_name
            data = in_path.read_bytes()
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                out_path.write_bytes(data)
            else:
                out_path.write_text(render_text(text, name), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a new domain from _template")
    parser.add_argument("name", help="domain name, e.g. profile")
    parser.add_argument("--force", action="store_true", help="overwrite if exists")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1] / "apps" / "backend" / "app" / "domains"
    src = root / "_template"
    if not src.exists():
        raise SystemExit(f"Template not found: {src}")
    dst = root / args.name
    if dst.exists() and not args.force:
        raise SystemExit(f"Destination exists: {dst}. Use --force to overwrite.")
    if dst.exists() and args.force:
        shutil.rmtree(dst)
    copy_tree(src, dst, args.name)
    print(f"Scaffolded domain '{args.name}' at {dst}")


if __name__ == "__main__":
    main()

