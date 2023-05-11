"""Implement madvr component."""
from collections.abc import Iterable
import logging
import asyncio

from madvr.madvr import Madvr
import voluptuous as vol

from homeassistant.components.remote import PLATFORM_SCHEMA, RemoteEntity
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TIMEOUT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_TIMEOUT): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType = None,
) -> None:
    """Set up platform."""
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    madvr_client = Madvr(
        host=host,
        logger=_LOGGER,
        connect_timeout=config.get(CONF_TIMEOUT),
    )
    # Open connection
    # await madvr_client.open_connection()

    async_add_entities(
        [
            MadvrCls(name, host, madvr_client),
        ]
    )


class MadvrCls(RemoteEntity):
    """Implements the interface for Madvr Remote in HA."""

    def __init__(
        self,
        name: str,
        host: str,
        madvr_client: Madvr = None,
    ) -> None:
        """MadVR Init."""
        self._name = name
        self._host = host
        self._state = False
        self._is_connected = False
        self.madvr_client = madvr_client

        self.attrs = {}

        self.command_queue = asyncio.Queue()
        asyncio.run(self.madvr_client.open_connection())
        asyncio.create_task(self.handle_queue())
    @property
    def should_poll(self):
        """Poll."""
        return False

    @property
    def name(self):
        """Name."""
        return self._name

    @property
    def host(self):
        """Host."""
        return self._host

    async def async_update(self):
        """Retrieve latest state."""
        # grab attrs from client
        self._state = self.madvr_client.is_on
        self.attrs = self.madvr_client.msg_dict

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        # Useful for making sensors
        return self.attrs

    @property
    def is_on(self):
        """Return the last known state."""
        return self._state

    async def handle_queue(self):
        """Handle items in command queue."""
        while True:
            # If there's a command in the queue, get it and send it
            while not self.command_queue.empty():
                command = await self.command_queue.get()
                await self.madvr_client.send_command(command)
                self.command_queue.task_done()

            # Process notifications, this will write attr to dict
            await self.madvr_client.read_notifications()
            
            await asyncio.sleep(0.1)  # sleep for a bit before doing next iteration

    async def async_turn_off(self, standby=False, **kwargs):
        """
        Send the power off command. Will tell envy to shut off and close the socket too

        send 'True' if you want standby instead
        """

        # Check if on so send_command does not open connection if its off already
        if self.is_on:
            await self.madvr_client.power_off(standby)
        else:
            await self.madvr_client.close_connection()
        self._state = False

    async def async_turn_on(self, **kwargs):
        """
        Send the power on command but not really.
        You must call this for it to connect
        """
        # Assumes madvr is already on
        await self.madvr_client.open_connection()
        self._state = True

    async def async_send_command(self, command: str, **kwargs):
        """Send commands to a device."""

        await self.command_queue.put(command)
