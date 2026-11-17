# Install a self-contained test bundle

The custom component includes its own private `pymadvr` library under
`custom_components/madvr/_vendor/pymadvr`. No library release, pip installation,
or `py-madvr2` requirement is needed. The beta component is `2.0.0b1`.
The bundled MIT license and `vendor_info.json` record the source commit,
whether the checkout was modified, source hashes, and generated file hashes.
Imports stay within the private package and do not replace a globally installed
library.

## Run tests

Use Python 3.14 and the pinned HA test plugin, which installs its matching Home
Assistant version (2026.10.4):

```sh
uv venv --python 3.14 .venv-test
uv pip install --python .venv-test/bin/python -r requirements-test.txt
.venv-test/bin/python -m pytest -q
```

The tests mock the Envy client and use real HA services and platform setup.
They do not verify a physical Envy or browser rendering.

From the integration repository, with the library checkout beside it:

```sh
python3 tools/sync_library.py
python3 tools/sync_library.py --check
python3 tools/prepare_test_bundle.py
```

The bundle builder checks the bundled library's hashes and version without
needing a separate library checkout. Maintainers can add
`--library /path/to/py-madvr` to also compare it with the source. The sync script
accepts the same option. The bundle builder refuses an existing output; use
`--output dist/madvr-bundled-test-2` for a new build.
The directory and ZIP contain `custom_components/madvr`, this document,
the README, a SHA256 inventory, an installer, and the example remote YAML files.
Only integration files are included: no credentials, virtualenvs, library tests,
or Python bytecode caches.

## Mounted Home Assistant config

Point the helper at the actual mounted config root (the directory containing
`.HA_VERSION` and `custom_components`). For example, from this repository:

```sh
python3 tools/install_mounted.py --config /Volumes/config --bundle dist/madvr-bundled-test
python3 tools/install_mounted.py --config /Volumes/config --bundle dist/madvr-bundled-test --install
```

The first command only checks. The second verifies the bundle, stages and hashes
the candidate, moves an existing `custom_components/madvr` in full to
`.madvr-backups/madvr-<timestamp>-<id>` in the config root, then installs and hashes
the candidate. It refuses symlink paths and changed targets, and restores the
previous folder if replacement or verification fails. The install receipt lists
the exact backup path and old/new SHA256 inventories. Keep that backup for rollback.
The copy does not modify HA configuration, integration entries, or other custom
components. From an extracted ZIP, run its `install_mounted.py` and pass the
extracted bundle directory to `--bundle`.

Restart Home Assistant using **Settings → System → Restart Home Assistant**
after installation; copying files alone does not reload Python modules.
Keep the Envy powered on, confirm the existing madVR integration loads, check
its sensors, and test a tap plus a hold on the included dashboard remote.
For a new setup, add **madVR Envy** under **Settings → Devices & services**.

Paste `examples/envy-remote.yaml` into a manual dashboard card and replace
`remote.envy` with your entity ID. Every button includes tap `KeyPress` and
hold `KeyHold`. This is one native long-press event, not continuous menu movement.
`hold_secs: 1` also maps a `KeyPress` to `KeyHold` in scripts or automations.
For repeated arrow movement, install Button Card through HACS and use
`examples/envy-remote-repeat.yaml`. Its arrows send repeated `KeyPress` commands
while held. Rendering and physical-device behavior remain unverified.

## Rollback

Use the exact paths printed by the installer or recorded in its receipt. Move
the current `custom_components/madvr` to an unused location outside
`custom_components`, then move the saved `.madvr-backups/madvr-<timestamp>-<id>`
back to `custom_components/madvr`. Restart Home Assistant again. Moving the
complete backup restores the previous library dependency declaration too.
Do not remove the integration from Devices & services: keeping its entry
preserves the existing configuration and entity IDs.
