"""Coordinator for handling data fetching and updates."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ._vendor.pymadvr.madvr import Madvr
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=0.1)

if TYPE_CHECKING:
    from . import MadVRConfigEntry


class MadVRCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Madvr coordinator for Envy (push-based API)."""

    config_entry: MadVRConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: Madvr,
    ) -> None:
        """Initialize madvr coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN)
        assert self.config_entry.unique_id
        self.mac = self.config_entry.unique_id
        self.client = client
        # Push updates populate data after the platforms are loaded.
        self.data = {}
        self._last_update_time = 0
        self._pending_update = None
        self._update_lock = asyncio.Lock()
        self.client.set_update_callback(self.handle_push_data)
        _LOGGER.debug("MadVRCoordinator initialized with mac: %s", self.mac)

    def handle_push_data(self, data: dict[str, Any]) -> None:
        """Handle new data pushed from the API with rate limiting."""
        self._pending_update = data
        self.hass.loop.call_soon_threadsafe(
            lambda: self.hass.create_task(self._process_update())
        )

    async def _process_update(self) -> None:
        """Process pending updates with rate limiting."""
        async with self._update_lock:
            if self._pending_update is None:
                return

            current_time = self.hass.loop.time()
            time_since_last = current_time - self._last_update_time

            if time_since_last < MIN_TIME_BETWEEN_UPDATES.total_seconds():
                await asyncio.sleep(
                    MIN_TIME_BETWEEN_UPDATES.total_seconds() - time_since_last
                )

            if self._pending_update is not None:
                data = self._pending_update
                self._pending_update = None
                self._last_update_time = self.hass.loop.time()

                self.async_set_updated_data(data)

    async def handle_coordinator_load(self) -> None:
        """Handle operations on integration load."""
        _LOGGER.debug("Using loop: %s", self.client.loop)
        try:
            await self.client.async_add_tasks()
        except Exception as e:
            _LOGGER.error("Failed to start background tasks: %s", e)
            self.cleanup()
            raise

    def cleanup(self) -> None:
        """Stop accepting client updates."""
        self._pending_update = None
        self.client.set_update_callback(None)
