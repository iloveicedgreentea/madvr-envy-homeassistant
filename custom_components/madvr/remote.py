"""Implement madvr component."""
import logging
import asyncio
from wakeonlan import send_magic_packet

from madvr.madvr import Madvr
import voluptuous as vol

from homeassistant.components.remote import PLATFORM_SCHEMA, RemoteEntity
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TIMEOUT, CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_MAC): cv.string,
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
    mac = config.get(CONF_MAC)
    madvr_client = Madvr(
        host=host,
        logger=_LOGGER,
        connect_timeout=config.get(CONF_TIMEOUT),
    )
    # Open connection
    # await madvr_client.open_connection()

    async_add_entities(
        [
            MadvrCls(hass, name, host, mac, madvr_client),
        ]
    )


class MadvrCls(RemoteEntity):
    """Implements the interface for Madvr Remote in HA."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        host: str,
        mac: str,
        madvr_client: Madvr = None,
    ) -> None:
        """MadVR Init."""
        self._name = name
        self._host = host
        self._state = False
        self._is_connected = False
        self.madvr_client = madvr_client
        self.mac = mac
        self.attrs = {}
        self.hass = hass
        self.tasks = []
        self.connection_event = self.madvr_client.connection_event

        self.command_queue = asyncio.Queue()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        task = self.hass.loop.create_task(self.madvr_client.open_connection())
        self.tasks.append(task)
        task = self.hass.loop.create_task(self.handle_queue())
        self.tasks.append(task)
        task = self.hass.loop.create_task(self.madvr_client.read_notifications())
        self.tasks.append(task)
    
    async def async_will_remove_from_hass(self) -> None:
        self.madvr_client.stop()
        for task in self.tasks:
            if not task.done():
                task.cancel()

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
        # msg dict would be cached if put below, so needs to get updated
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
            await self.connection_event.wait()
            # send all commands in queue
            while not self.command_queue.empty():
                command = await self.command_queue.get()
                try:
                    await self.madvr_client.send_command(command)
                except AttributeError:
                    _LOGGER.warning("issue sending command")
                except Exception as err:
                    _LOGGER.error("Unexpected error when sending command: %s", err)
                finally:
                    self.command_queue.task_done()

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
        send_magic_packet(self.mac)
        await self.madvr_client.open_connection()
        self._state = True

    async def async_send_command(self, command: str, **kwargs):
        """Send commands to a device."""

        await self.command_queue.put(command)
