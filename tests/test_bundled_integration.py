"""Exercise the self-contained integration through real Home Assistant services.

Run with pytest-homeassistant-custom-component and --asyncio-mode=auto.
Only the Envy client boundary is mocked; HA loads the actual platforms.
"""

import sys
from importlib import import_module
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
import yaml
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("enable_custom_integrations"),
]


async def test_setup_remote_actions_and_unload(hass, monkeypatch):
    """Setup must work without installing pymadvr, including the remote hold path."""
    client = MagicMock()
    client.loop = hass.loop
    client.is_on = True
    client.async_add_tasks = AsyncMock()
    client.async_cancel_tasks = AsyncMock()
    client.close_connection = AsyncMock()
    client.add_command_to_queue = AsyncMock()
    entry = MockConfigEntry(
        domain="madvr",
        title="Envy",
        unique_id="00:11:22:33:44:55",
        data={"host": "192.0.2.1", "port": 44077},
    )
    entry.add_to_hass(hass)

    # A globally installed package must never be necessary for this bundle.
    monkeypatch.setitem(sys.modules, "pymadvr", None)
    # HA's fixture mounts its own regular custom_components test package.
    components = import_module("custom_components")
    monkeypatch.setattr(
        components,
        "__path__",
        [str(Path(__file__).parents[1] / "custom_components"), *components.__path__],
    )
    integration = import_module("custom_components.madvr")
    config_flow = import_module("custom_components.madvr.config_flow")
    assert integration.Madvr is config_flow.Madvr
    assert integration.Madvr.__module__.startswith("custom_components.madvr._vendor.")

    with patch.object(integration, "Madvr", return_value=client):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        client.async_add_tasks.assert_awaited_once()
        (entity_id,) = hass.states.async_entity_ids("remote")
        assert hass.states.get(entity_id).state == "on"

        async def send(command, **kwargs):
            await hass.services.async_call(
                "remote",
                "send_command",
                {"entity_id": entity_id, "command": command, **kwargs},
                blocking=True,
            )

        await send("UP")
        await send("KeyPress, DOWN", hold_secs=1)
        await send("KeyHold, LEFT")
        await send("RIGHT", num_repeats=3, delay_secs=0)
        assert client.add_command_to_queue.await_args_list == [
            call(["KeyPress", "UP"]),
            call(["KeyHold", "DOWN"]),
            call(["KeyHold", "LEFT"]),
            call(["KeyPress", "RIGHT"]),
            call(["KeyPress", "RIGHT"]),
            call(["KeyPress", "RIGHT"]),
        ]

        # Exercise every pasted dashboard action using HA's actual service schema.
        client.add_command_to_queue.reset_mock()
        example = Path(__file__).parents[1] / "examples/envy-remote.yaml"
        cards = yaml.safe_load(example.read_text())["cards"]
        for card in cards:
            for action_name in ("tap_action", "hold_action"):
                action = card[action_name]
                assert action["perform_action"] == "remote.send_command"
                await send(action["data"]["command"])
        assert client.add_command_to_queue.await_count == 26

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.NOT_LOADED
        client.stop.assert_called_once()
        client.async_cancel_tasks.assert_not_awaited()
        client.close_connection.assert_awaited_once()
        client.set_update_callback.assert_called_with(None)


@pytest.mark.parametrize(
    "failure", [None, TimeoutError(), OSError("Connection refused")]
)
async def test_config_connection_always_closes_client(hass, monkeypatch, failure):
    """Discovery closes its temporary client on success and connection errors."""
    components = import_module("custom_components")
    monkeypatch.setattr(
        components,
        "__path__",
        [str(Path(__file__).parents[1] / "custom_components"), *components.__path__],
    )
    config_flow = import_module("custom_components.madvr.config_flow")
    client = MagicMock()
    client.open_connection = AsyncMock(side_effect=failure)
    client.close_connection = AsyncMock()
    client.async_add_tasks = AsyncMock()
    client.connected = True
    client.mac_address = "00:11:22:33:44:55"

    with patch.object(config_flow, "Madvr", return_value=client):
        if failure is None:
            assert (
                await config_flow.test_connection(hass, "192.0.2.1", 44077)
                == client.mac_address
            )
        else:
            with pytest.raises(config_flow.CannotConnect):
                await config_flow.test_connection(hass, "192.0.2.1", 44077)

    client.open_connection.assert_awaited_once()
    client.async_add_tasks.assert_not_awaited()
    client.stop.assert_called_once()
    client.close_connection.assert_awaited_once()
