"""Coordinator for handling data fetching and updates."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any

from madvr.madvr import Madvr

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import Throttle

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Minimum time between updates
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
        # this does not use poll/refresh, so we need to set this to not None on init
        self.data = {}
        # Rate limiting
        self._last_update_time = 0
        self._pending_update = None
        self._update_lock = asyncio.Lock()
        # this passes a callback to the client to push new data to the coordinator
        self.client.set_update_callback(self.handle_push_data)
        _LOGGER.debug("MadVRCoordinator initialized with mac: %s", self.mac)

    def handle_push_data(self, data: dict[str, Any]) -> None:
        """Handle new data pushed from the API with rate limiting."""
        # Safety check: reject extremely large data payloads
        try:
            import sys
            data_size = sys.getsizeof(data)
            if data_size > 1_000_000:  # 1MB limit
                _LOGGER.warning("Rejecting oversized data payload: %d bytes", data_size)
                return
        except Exception:
            pass  # Continue if size check fails
            
        # Store the pending update and schedule processing
        self._pending_update = data
        # Use Home Assistant's event loop to schedule the update
        self.hass.loop.call_soon_threadsafe(
            lambda: self.hass.create_task(self._process_update())
        )

    async def _process_update(self) -> None:
        """Process pending updates with rate limiting."""
        async with self._update_lock:
            if self._pending_update is None:
                return
                
            # Check rate limit
            current_time = self.hass.loop.time()
            time_since_last = current_time - self._last_update_time
            
            if time_since_last < MIN_TIME_BETWEEN_UPDATES.total_seconds():
                # Schedule update for later
                await asyncio.sleep(MIN_TIME_BETWEEN_UPDATES.total_seconds() - time_since_last)
            
            # Process the update
            if self._pending_update is not None:
                data = self._pending_update
                self._pending_update = None
                self._last_update_time = self.hass.loop.time()
                
                # Only update if data has actually changed
                if data != self.data:
                    self.async_set_updated_data(data)

    async def handle_coordinator_load(self) -> None:
        """Handle operations on integration load."""
        _LOGGER.debug("Using loop: %s", self.client.loop)
        try:
            # tell the library to start background tasks
            await self.client.async_add_tasks()
            _LOGGER.debug("Added %s tasks to client", len(self.client.tasks))
        except Exception as e:
            _LOGGER.error("Failed to start background tasks: %s", e)
            # Clean up on failure
            self.cleanup()
            raise
        
    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        # Clear pending updates
        self._pending_update = None
        # Clear the update callback to break circular references
        if hasattr(self.client, 'set_update_callback'):
            self.client.set_update_callback(None)
