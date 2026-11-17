"""Verify mounted installation backups, integrity checks, and failure recovery."""

from pathlib import Path
import runpy
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).parents[1]
INSTALLER = runpy.run_path(str(ROOT / "tools/install_mounted.py"))


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    output = tmp_path_factory.mktemp("madvr-bundle").resolve() / "bundle"
    subprocess.run(
        [sys.executable, str(ROOT / "tools/prepare_test_bundle.py"), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    return output


@pytest.fixture
def config(tmp_path):
    config = tmp_path.resolve() / "ha-config"
    component = config / "custom_components/madvr"
    (component / "translations").mkdir(parents=True)
    (config / ".HA_VERSION").write_text("2026.9.1\n")
    (component / "__init__.py").write_text("# previous component\n")
    (component / "translations/en.json").write_text('{"old": true}\n')
    (component / "old-cache.pyc").write_bytes(b"previous cache")
    return config


def install(monkeypatch, config, bundle, *, apply=False):
    argv = ["install_mounted.py", "--config", str(config), "--bundle", str(bundle)]
    if apply:
        argv.append("--install")
    monkeypatch.setattr(sys, "argv", argv)
    INSTALLER["main"]()


def test_dry_run_and_install_preserve_complete_backup(monkeypatch, config, bundle):
    original = INSTALLER["inventory"](config)
    install(monkeypatch, config, bundle)
    assert INSTALLER["inventory"](config) == original

    previous = INSTALLER["inventory"](config / "custom_components/madvr")
    install(monkeypatch, config, bundle, apply=True)
    assert INSTALLER["inventory"](config / "custom_components/madvr") == INSTALLER["verify_bundle"](bundle)
    backups = list((config / ".madvr-backups").iterdir())
    assert len(backups) == 1
    assert INSTALLER["inventory"](backups[0]) == previous
    assert len(list(config.glob(".madvr-install-*.json"))) == 1


def test_corrupted_bundle_leaves_original_untouched(monkeypatch, config, bundle, tmp_path):
    corrupted = tmp_path.resolve() / "corrupted"
    shutil.copytree(bundle, corrupted)
    (corrupted / "custom_components/madvr/__init__.py").write_text("# corrupted\n")
    original = INSTALLER["inventory"](config)
    with pytest.raises(SystemExit, match="2"):
        install(monkeypatch, config, corrupted, apply=True)
    assert INSTALLER["inventory"](config) == original


def test_symlink_config_is_rejected(monkeypatch, config, bundle, tmp_path):
    alias = tmp_path.resolve() / "config-link"
    alias.symlink_to(config, target_is_directory=True)
    original = INSTALLER["inventory"](config)
    with pytest.raises(SystemExit, match="2"):
        install(monkeypatch, alias, bundle, apply=True)
    assert INSTALLER["inventory"](config) == original


def test_failed_replacement_restores_original(monkeypatch, config, bundle):
    previous = INSTALLER["inventory"](config / "custom_components/madvr")
    original_rename = Path.rename

    def fail_staging_rename(path, target):
        if path.name.startswith(".madvr-stage-"):
            raise OSError("Simulated mounted-volume rename failure")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_staging_rename)
    with pytest.raises(SystemExit, match="2"):
        install(monkeypatch, config, bundle, apply=True)
    assert INSTALLER["inventory"](config / "custom_components/madvr") == previous
    assert list((config / ".madvr-backups").iterdir()) == []
    assert list(config.glob(".madvr-stage-*"))


def test_failed_receipt_restores_original(monkeypatch, config, bundle):
    previous = INSTALLER["inventory"](config / "custom_components/madvr")
    original_write_text = Path.write_text

    def fail_receipt_write(path, *args, **kwargs):
        if path.name.startswith(".madvr-install-"):
            raise OSError("Simulated receipt write failure")
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_receipt_write)
    with pytest.raises(SystemExit, match="2"):
        install(monkeypatch, config, bundle, apply=True)
    assert INSTALLER["inventory"](config / "custom_components/madvr") == previous
    assert list((config / ".madvr-backups").iterdir()) == []
    failed, = config.glob(".madvr-failed-*")
    assert INSTALLER["inventory"](failed) == INSTALLER["verify_bundle"](bundle)
