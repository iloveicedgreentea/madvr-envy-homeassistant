"""The madvr-envy integration."""

from __future__ import annotations

import logging

from madvr.madvr import Madvr

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import MadVRCoordinator

PLATFORMS: list[Platform] = [Platform.REMOTE]

type MadVRConfigEntry = ConfigEntry[MadVRCoordinator]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: MadVRConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    madVRClient = Madvr(
        host=entry.data[CONF_HOST],
        logger=_LOGGER,
        port=entry.data[CONF_PORT],
        mac=entry.data[CONF_MAC],
        connect_timeout=10,
        loop=hass.loop,
    )
    coordinator = MadVRCoordinator(
        hass,
        entry,
        madVRClient,
        name=name,
    )
    hass.data.setdefault(DOMAIN, {})
    await coordinator.async_refresh()
    entry.runtime_data = coordinator
    hass.data[DOMAIN]["entry_id"] = entry.entry_id

    await coordinator.async_config_entry_first_refresh()

    # Forward the entry setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.add_update_listener(async_reload_entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MadVRConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: MadVRCoordinator = entry.runtime_data
        if coordinator:
            await coordinator.async_handle_unload()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: MadVRConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
