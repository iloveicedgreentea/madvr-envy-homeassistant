"""The madvr-envy integration."""

from __future__ import annotations

import logging

from madvr.madvr import Madvr

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant

from .coordinator import MadVRCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.REMOTE, Platform.SENSOR]


type MadVRConfigEntry = ConfigEntry[MadVRCoordinator]

_LOGGER = logging.getLogger(__name__)


async def async_handle_unload(coordinator: MadVRCoordinator) -> None:
    """Handle unload."""
    _LOGGER.debug("Integration unloading")
    # Clean up coordinator resources first
    coordinator.cleanup()
    coordinator.client.stop()
    await coordinator.client.async_cancel_tasks()
    _LOGGER.debug("Integration closing connection")
    await coordinator.client.close_connection()
    _LOGGER.debug("Unloaded")


async def async_setup_entry(hass: HomeAssistant, entry: MadVRConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    assert entry.unique_id
    
    # Check if this entry is already being set up to prevent duplicate connections
    if hasattr(entry, "_setup_lock"):
        _LOGGER.warning("Setup already in progress for %s", entry.unique_id)
        return False
        
    entry._setup_lock = True
    
    try:
        madVRClient = Madvr(
            host=entry.data[CONF_HOST],
            logger=_LOGGER,
            port=entry.data[CONF_PORT],
            mac=entry.unique_id,
            connect_timeout=10,
            loop=hass.loop,
        )
        coordinator = MadVRCoordinator(hass, madVRClient)

        entry.runtime_data = coordinator

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        async def handle_unload(event: Event) -> None:
            """Handle unload."""
            await async_handle_unload(coordinator=coordinator)

        # listen for core stop event
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, handle_unload)

        # Add a small delay before starting connection to avoid overwhelming the system
        # This helps when multiple integrations are starting simultaneously
        await hass.async_add_executor_job(lambda: None)
        
        # handle loading operations
        await coordinator.handle_coordinator_load()
        return True
    finally:
        if hasattr(entry, "_setup_lock"):
            delattr(entry, "_setup_lock")


async def async_unload_entry(hass: HomeAssistant, entry: MadVRConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: MadVRCoordinator = entry.runtime_data
        await async_handle_unload(coordinator=coordinator)

    return unload_ok
