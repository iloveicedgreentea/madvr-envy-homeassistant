#!/usr/bin/env python3
"""Reproduce the private library copy from a reviewed py-madvr checkout."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

PACKAGE_FILES = (
    "__init__.py",
    "commands.py",
    "connection_pool.py",
    "consts.py",
    "errors.py",
    "madvr.py",
    "notifications.py",
    "simple_pool.py",
    "wol.py",
    "py.typed",
)


def library_version(source: bytes) -> str:
    """Read setup metadata without executing it."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "setup":
                for keyword in node.keywords:
                    if keyword.arg == "version":
                        value = ast.literal_eval(keyword.value)
                        if isinstance(value, str):
                            return value
    raise ValueError("Expected a literal library version in setup.py")


def expected_files(library: Path) -> dict[str, bytes]:
    """Keep source and generated hashes, and record the namespace conversion."""
    package = library / "pymadvr"
    if {p.name for p in package.iterdir() if p.is_file()} != set(PACKAGE_FILES):
        raise ValueError("Library files changed; review PACKAGE_FILES before syncing")
    originals = {name: (package / name).read_bytes() for name in PACKAGE_FILES}
    originals["LICENSE"] = (library / "LICENSE").read_bytes()
    originals["setup.py"] = (library / "setup.py").read_bytes()
    generated = {}
    for name in PACKAGE_FILES:
        data = originals[name]
        if name.endswith(".py"):
            code = re.sub(r"(?m)^from pymadvr\.", "from .", data.decode())
            for node in ast.walk(ast.parse(code)):
                if isinstance(node, ast.Import) and any(
                    alias.name.split(".")[0] == "pymadvr" for alias in node.names
                ):
                    raise ValueError(f"Unsupported absolute library import: {name}")
                if (
                    isinstance(node, ast.ImportFrom)
                    and not node.level
                    and (
                        node.module == "pymadvr"
                        or (node.module or "").startswith("pymadvr.")
                    )
                ):
                    raise ValueError(f"Unsupported absolute library import: {name}")
            data = code.encode()
        generated[name] = data
    generated["LICENSE"] = originals["LICENSE"]
    source_hash = hashlib.sha256()
    for name, data in sorted(originals.items()):
        source_hash.update(name.encode() + b"\0" + data + b"\0")
    metadata = {
        "source_repository": "https://github.com/iloveicedgreentea/py-madvr",
        "source_commit": subprocess.check_output(
            ["git", "-C", str(library), "rev-parse", "HEAD"], text=True
        ).strip(),
        "source_modified": bool(
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(library),
                    "status",
                    "--porcelain",
                    "--",
                    "pymadvr",
                    "LICENSE",
                    "setup.py",
                ],
                text=True,
            ).strip()
        ),
        "library_version": library_version(originals["setup.py"]),
        "transform": "Replace top-level 'from pymadvr.' imports with 'from .'",
        "source_sha256": source_hash.hexdigest(),
        "source_files_sha256": {
            name: hashlib.sha256(data).hexdigest()
            for name, data in sorted(originals.items())
        },
        "vendored_files_sha256": {
            name: hashlib.sha256(data).hexdigest()
            for name, data in sorted(generated.items())
        },
    }
    generated["vendor_info.json"] = (
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {
        "__init__.py": b'"""Private dependencies for the madVR integration."""\n',
        **{f"pymadvr/{name}": data for name, data in generated.items()},
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=root.parent / "py-madvr")
    parser.add_argument("--check", action="store_true", help="Verify without writing")
    args = parser.parse_args()
    try:
        expected = expected_files(args.library.expanduser().resolve())
    except (OSError, ValueError, subprocess.CalledProcessError) as err:
        parser.error(str(err))
    destination = root / "custom_components" / "madvr" / "_vendor"
    existing = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    stale = existing - expected.keys()
    if stale:
        parser.error(
            "Unexpected vendor files require review: " + ", ".join(sorted(stale))
        )
    mismatches = [
        name
        for name, data in expected.items()
        if not (destination / name).is_file()
        or (destination / name).read_bytes() != data
    ]
    if args.check:
        if mismatches:
            print("Vendored library differs: " + ", ".join(mismatches))
            return 1
        print("Vendored library matches source and provenance metadata")
        return 0
    for name, data in expected.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print("Synced private pymadvr package, license, and provenance metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
