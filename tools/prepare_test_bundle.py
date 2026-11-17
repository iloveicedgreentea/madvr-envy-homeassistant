#!/usr/bin/env python3
"""Build a fresh self-contained madVR test bundle without publishing."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def verify_vendor(component: Path, version: str) -> None:
    """Check the bundled library without requiring its source checkout."""
    package = component / "_vendor" / "pymadvr"
    metadata = json.loads((package / "vendor_info.json").read_text())
    if metadata["library_version"] != version:
        raise ValueError("Component and bundled library versions differ")
    actual = {
        path.relative_to(package).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in package.rglob("*")
        if path.is_file()
        and path.name != "vendor_info.json"
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    }
    if actual != metadata["vendored_files_sha256"]:
        raise ValueError("Bundled library SHA256 inventory mismatch")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--library", type=Path, help="Also compare with this source checkout"
    )
    parser.add_argument(
        "--output", type=Path, default=root / "dist" / "madvr-bundled-test"
    )
    args = parser.parse_args()
    library = args.library.expanduser().resolve() if args.library else None
    output = args.output.expanduser().resolve()
    archive = output.with_suffix(output.suffix + ".zip")
    component = root / "custom_components" / "madvr"
    if output.exists() or archive.exists():
        parser.error(f"Output exists; choose a fresh path: {output}")
    sources = [component, root / "examples", root / "tools"]
    if library:
        sources.append(library)
    for source in sources:
        if output == source or output.is_relative_to(source):
            parser.error(f"Output must be outside the source tree: {source}")
    manifest = json.loads((component / "manifest.json").read_text())
    if manifest.get("requirements") != []:
        parser.error("Expected requirements: [] for the bundled integration")
    try:
        verify_vendor(component, manifest["version"])
    except (OSError, ValueError, KeyError, TypeError) as err:
        parser.error(str(err))
    if library:
        subprocess.run(
            [
                sys.executable,
                str(root / "tools" / "sync_library.py"),
                "--library",
                str(library),
                "--check",
            ],
            check=True,
        )
    shutil.copytree(
        component,
        output / "custom_components" / "madvr",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copytree(root / "examples", output / "examples")
    shutil.copy2(root / "readme.md", output / "README.md")
    shutil.copy2(root / "docs" / "testing.md", output / "TESTING.md")
    shutil.copy2(root / "tools" / "install_mounted.py", output / "install_mounted.py")
    inventory = {
        "component_version": manifest["version"],
        "files": {
            path.relative_to(output).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
    }
    (output / "bundle.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    )
    shutil.make_archive(str(output), "zip", root_dir=output)
    print(f"Bundle: {output}\nZIP: {archive}\nNothing installed or published.")


if __name__ == "__main__":
    main()
