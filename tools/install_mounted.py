#!/usr/bin/env python3
"""Verify and optionally install only madvr into an explicitly mounted HA config."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import uuid


def inventory(directory: Path) -> dict[str, str]:
    """Hash a directory without following symlinks or accepting special files."""
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"Expected a real directory: {directory}")
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Refusing symlink: {path}")
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        elif not path.is_dir():
            raise ValueError(f"Refusing special file: {path}")
    return result


def real_path(path: Path) -> Path:
    """Reject symlink components before resolving the requested path."""
    absolute = path.expanduser().absolute()
    for ancestor in (absolute, *absolute.parents):
        if ancestor.is_symlink():
            raise ValueError(f"Refusing symlink path: {ancestor}")
    return absolute.resolve()


def verify_bundle(bundle: Path) -> dict[str, str]:
    """Verify every bundle file and reject extra files and unsafe paths."""
    actual = inventory(bundle)
    metadata = json.loads((bundle / "bundle.json").read_text())
    expected = metadata["files"]
    if not isinstance(expected, dict):
        raise ValueError("Invalid bundle inventory")
    for name in expected:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != name:
            raise ValueError(f"Unsafe bundle path: {name}")
    actual.pop("bundle.json", None)
    if actual != expected:
        raise ValueError("Bundle SHA256 inventory mismatch")
    component = bundle / "custom_components" / "madvr"
    manifest = json.loads((component / "manifest.json").read_text())
    if manifest.get("domain") != "madvr" or manifest.get("requirements") != []:
        raise ValueError(
            "Expected self-contained madvr component with requirements: []"
        )
    if manifest.get("version") != metadata.get("component_version"):
        raise ValueError("Component version differs from bundle metadata")
    if not (component / "_vendor" / "pymadvr" / "vendor_info.json").is_file():
        raise ValueError("Missing vendored library provenance")
    return {
        name.removeprefix("custom_components/madvr/"): digest
        for name, digest in expected.items()
        if name.startswith("custom_components/madvr/")
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", required=True, type=Path, help="Mounted HA config root"
    )
    parser.add_argument(
        "--bundle", required=True, type=Path, help="Extracted bundle directory"
    )
    parser.add_argument(
        "--install", action="store_true", help="Install; default only verifies"
    )
    args = parser.parse_args()
    try:
        config = real_path(args.config)
        bundle = real_path(args.bundle)
        version_file = config / ".HA_VERSION"
        components = config / "custom_components"
        if version_file.is_symlink() or not version_file.is_file():
            raise ValueError(f"Missing real .HA_VERSION file in {config}")
        if components.is_symlink() or not components.is_dir():
            raise ValueError(f"Missing real custom_components directory in {config}")
        if bundle == config or bundle.is_relative_to(config):
            raise ValueError("Bundle must be outside the mounted config")
        expected = verify_bundle(bundle)
        destination = components / "madvr"
        if destination.is_symlink() or (
            destination.exists() and not destination.is_dir()
        ):
            raise ValueError(
                f"Refusing non-directory integration target: {destination}"
            )
        previous = inventory(destination) if destination.exists() else None
        backup_root = config / ".madvr-backups"
        if backup_root.is_symlink() or (
            backup_root.exists() and not backup_root.is_dir()
        ):
            raise ValueError(f"Refusing backup target: {backup_root}")
        token = (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            + "-"
            + uuid.uuid4().hex[:8]
        )
        backup = backup_root / ("madvr-" + token)
        staging = config / (".madvr-stage-" + token)
        if (
            staging.exists()
            or staging.is_symlink()
            or backup.exists()
            or backup.is_symlink()
        ):
            raise ValueError("Staging or backup path already exists")
        print(
            f"Verified {len(expected)} component files; HA {version_file.read_text().strip()}"
        )
        print(
            f"Target: {destination}\nBackup: {backup if previous is not None else '(fresh install)'}"
        )
        if not args.install:
            print(
                "Dry run complete. Add --install to copy and replace madvr. HA is not restarted."
            )
            return
        shutil.copytree(bundle / "custom_components" / "madvr", staging)
        if inventory(staging) != expected:
            raise ValueError(f"Staging verification failed; retained at {staging}")
        # Recheck before replacing in case the mounted target changed during copying.
        if (inventory(destination) if destination.exists() else None) != previous:
            raise ValueError(
                f"Target changed during staging; candidate retained at {staging}"
            )
        moved_old = False
        installed = False
        try:
            if previous is not None:
                backup_root.mkdir(exist_ok=True)
                destination.rename(backup)
                moved_old = True
                if inventory(backup) != previous:
                    raise ValueError("Backup verification failed")
            staging.rename(destination)
            installed = True
            if inventory(destination) != expected:
                raise ValueError("Installed component verification failed")
            receipt = config / (".madvr-install-" + token + ".json")
            receipt.write_text(
                json.dumps(
                    {
                        "target": str(destination),
                        "backup": str(backup) if previous is not None else None,
                        "previous_files_sha256": previous,
                        "installed_files_sha256": expected,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
        except Exception:
            if installed:
                failed = config / (".madvr-failed-" + token)
                destination.rename(failed)
                print(f"Failed candidate retained at {failed}")
            if moved_old:
                backup.rename(destination)
                print(f"Restored previous madvr at {destination}")
            raise
        print(
            f"Installed and SHA256 verified. Receipt: {receipt}\nRestart Home Assistant to load it."
        )
    except (OSError, ValueError, KeyError, TypeError) as err:
        parser.error(str(err))


if __name__ == "__main__":
    main()
