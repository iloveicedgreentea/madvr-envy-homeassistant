"""The madvr-envy integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant

from ._vendor.pymadvr.madvr import Madvr
from .coordinator import MadVRCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.REMOTE, Platform.SENSOR]


type MadVRConfigEntry = ConfigEntry[MadVRCoordinator]

_LOGGER = logging.getLogger(__name__)


async def async_handle_unload(coordinator: MadVRCoordinator) -> None:
    """Stop updates and close the client."""
    coordinator.cleanup()
    coordinator.client.stop()
    await coordinator.client.close_connection()


async def async_setup_entry(hass: HomeAssistant, entry: MadVRConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    assert entry.unique_id
    client = Madvr(
        host=entry.data[CONF_HOST],
        logger=_LOGGER,
        port=entry.data[CONF_PORT],
        mac=entry.unique_id,
        connect_timeout=10,
        loop=hass.loop,
    )
    coordinator = MadVRCoordinator(hass, client)
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_stop(event: Event) -> None:
        """Close the client when Home Assistant stops."""
        await async_handle_unload(coordinator)

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, handle_stop)
    )
    await coordinator.handle_coordinator_load()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MadVRConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: MadVRCoordinator = entry.runtime_data
        await async_handle_unload(coordinator=coordinator)

    return unload_ok
