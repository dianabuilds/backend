import json
from pathlib import Path
import shutil

root = Path(r"E:/code/caves/backend/apps/web")
manifest_path = root / "dist" / "client" / ".vite" / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
html_template = (root / "index.html").read_text(encoding="utf-8")
public_entry = manifest["src/public-entry.tsx"]

css_links = []
if public_entry.get("css"):
    for css in public_entry["css"]:
        css_links.append(f'    <link rel="stylesheet" crossorigin href="/{css}">')

imports_block = []
processed = set()
for name in public_entry.get("imports", []):
    entry = manifest.get(name)
    if not entry:
        continue
    file = entry.get("file")
    if not file or file in processed:
        continue
    imports_block.append(f'    <link rel="modulepreload" crossorigin href="/{file}">')
    processed.add(file)

public_file = public_entry["file"]
assets_block = "\n".join(
    css_links
    + imports_block
    + [f'    <script type="module" crossorigin src="/{public_file}"></script>']
)
updated_html = html_template.replace(
    '    <script type="module" src="/src/main.tsx"></script>', assets_block
)

output_path = root / "dist" / "client" / "index.html"
output_path.write_text(updated_html, encoding="utf-8")

manifest_copy = root / "dist" / "client" / "manifest.json"
shutil.copyfile(manifest_path, manifest_copy)
