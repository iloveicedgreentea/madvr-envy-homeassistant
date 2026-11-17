# madVR Envy for Home Assistant

Control an Envy over the local network and use its signal, aspect-ratio, HDR,
temperature, and power sensors in automations.

## Install

Add this repository to HACS as a custom integration, or copy the entire
`custom_components/madvr` folder into your Home Assistant config. Restart Home
Assistant, then add **madVR Envy** under **Settings → Devices & services** while
the Envy is powered on. Keep an existing integration entry when upgrading.

Version `2.0.0b1` bundles the matching `pymadvr` library privately. It needs no
separate library installation or PyPI release. See [bundle installation and
rollback](docs/testing.md) for the ZIP builder and mounted-volume installer.

## Remote commands

Use `remote.send_command` with the Envy's remote entity. Existing comma-separated
commands still work:

```yaml
action: remote.send_command
target:
  entity_id: remote.envy
data:
  command: "OpenMenu, Profiles"
```

Source and display profiles use `ActivateProfile, SOURCE, 2` and
`ActivateProfile, DISPLAY, 1`. Custom profile groups use their numeric group ID,
for example `ActivateProfile, 1, 2`. Use the Envy's actual profile IDs.

The bundled library also supports aspect-ratio overrides, on-screen alerts,
profile enumeration and editing, and option query/change/inherit commands.
See the [library documentation](https://github.com/iloveicedgreentea/py-madvr)
and [Envy IP control reference](https://madvr.com/EnvyIpControl.pdf).

## Dashboard remote and held keys

Paste [`examples/envy-remote.yaml`](examples/envy-remote.yaml) into a dashboard
Manual card and replace `remote.envy` with your entity ID. All 13 buttons include
tap `KeyPress` and hold `KeyHold` actions.

**`KeyHold` is one Envy long-press event. It does not repeatedly move through a
menu.** The standard HA Button card fires its hold action once after release.
What a native long press does depends on the Envy key and current menu.

To add a native long press to an existing button, put this beside its
`tap_action`:

```yaml
hold_action:
  action: perform-action
  perform_action: remote.send_command
  target:
    entity_id: remote.envy
  data:
    command: "KeyHold, UP"
```

Scripts and automations can use `hold_secs: 1` with `KeyPress` to send the same
native long-press event. `num_repeats` and `delay_secs` control a fixed number of
commands; they do not track when a dashboard button is released.

For arrows that **repeat while held**, install **Button Card** through HACS and
use [`examples/envy-remote-repeat.yaml`](examples/envy-remote-repeat.yaml). Only
the four arrows use custom cards and repeat `KeyPress` every 300 milliseconds.
Other buttons keep their standard card and native long-press action. This is a
separate example, so existing dashboards do not change on upgrade. Browser
rendering and physical Envy behavior still need user testing.

## Upgrade notes

- Copy the complete component, including `_vendor`; copying only the top-level
  Python files will no longer work.
- Use the UI integration setup. YAML platform setup and `scan_interval` are not
  supported by this version.
- Commands containing CR, LF, NUL, or embedded double quotes are rejected.
- A `KeyPress` with `hold_secs >= 1` now sends `KeyHold`. Repeats and delays are
  now applied instead of ignored.

Existing config entries and entity IDs are retained.
