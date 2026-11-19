#!/usr/bin/env python3
"""Read-only verification of this distribution's reusable source inventory."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
manifest = json.loads((root / "upgrades/releases/3.6.0/inventory.json").read_text())
failures = []
for entry in manifest["files"]:
    name = entry["path"]
    path = root / name
    if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
        failures.append(f"Missing/unsafe source: {name}")
    elif hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        failures.append(f"Changed source: {name}")
if failures:
    raise SystemExit("\n".join(failures))
print(f"Verified {len(manifest['files'])} reusable source files; no project migration or activation implied.")
