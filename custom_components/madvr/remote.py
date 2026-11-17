"""Support for madVR remote control."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
import logging
from typing import Any

from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_HOLD_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_HOLD_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MadVRConfigEntry
from ._vendor.pymadvr.commands import KeyPress
from .coordinator import MadVRCoordinator
from .entity import MadVREntity

_LOGGER = logging.getLogger(__name__)

REMOTE_KEYS = frozenset(key.value.decode("ascii") for key in KeyPress)


def _normalize_command(command: Iterable[str], hold_secs: float) -> list[str]:
    """Normalize HA-friendly key syntax and apply Envy's key-hold event."""
    parts = [part.strip() for part in command]
    if not parts:
        raise ValueError("At least one command is required")

    # Retain the integration's comma-separated command syntax.
    if len(parts) == 1 and "," in parts[0]:
        parts = [part.strip() for part in parts[0].split(",")]

    if len(parts) == 1 and parts[0].upper() in REMOTE_KEYS:
        parts = ["KeyPress", parts[0].upper()]

    if parts[0].casefold() == "keypress" and hold_secs >= 1:
        parts[0] = "KeyHold"

    return parts


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MadVRConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the madVR remote."""
    coordinator = entry.runtime_data
    async_add_entities([MadvrRemote(coordinator)])


class MadvrRemote(MadVREntity, RemoteEntity):
    """Remote entity for the madVR integration."""

    _attr_name = None

    def __init__(
        self,
        coordinator: MadVRCoordinator,
    ) -> None:
        """Initialize the remote entity."""
        super().__init__(coordinator)
        self.madvr_client = coordinator.client
        self._attr_unique_id = coordinator.mac
        self.coordinator = coordinator

    @property
    def is_on(self) -> bool:
        """Return true if the device is on."""
        return self.madvr_client.is_on

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the device."""
        _LOGGER.debug("Turning off")
        try:
            await self.madvr_client.power_off()
        except (ConnectionError, NotImplementedError) as err:
            _LOGGER.error("Failed to turn off device %s", err)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the device."""
        _LOGGER.debug("Turning on device")

        try:
            await self.madvr_client.power_on(mac=self.coordinator.mac)
        except (ConnectionError, NotImplementedError) as err:
            _LOGGER.error("Failed to turn on device %s", err)

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to one device."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay_secs = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        hold_secs = kwargs.get(ATTR_HOLD_SECS, DEFAULT_HOLD_SECS)
        normalized_command = _normalize_command(command, hold_secs)

        _LOGGER.debug(
            "Queueing command %s (%s repeat(s), hold_secs=%s)",
            normalized_command,
            num_repeats,
            hold_secs,
        )
        try:
            for repeat in range(num_repeats):
                await self.madvr_client.add_command_to_queue(normalized_command)
                if repeat < num_repeats - 1 and delay_secs > 0:
                    await asyncio.sleep(delay_secs)
        except (ConnectionError, NotImplementedError) as err:
            _LOGGER.error("Failed to send command %s", err)
