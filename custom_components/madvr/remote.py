"""Implement madvr component."""

import logging
import asyncio
from wakeonlan import send_magic_packet

from madvr.madvr import Madvr
import voluptuous as vol

from homeassistant.components.remote import PLATFORM_SCHEMA, RemoteEntity
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_TIMEOUT,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
)
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
        vol.Required(CONF_SCAN_INTERVAL): cv.time_period,
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
        self.madvr_client.is_on = False
        self.mac = mac
        self.hass = hass
        self.tasks = []
        self.connection_event = self.madvr_client.connection_event

        self.command_queue = asyncio.Queue()
        self.stop_processing_commands = asyncio.Event()
        # pass in the method to write state immediately
        self.madvr_client.set_update_callback(self.async_write_ha_state)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        task_con = self.hass.loop.create_task(self.ping_until_alive())
        self.tasks.append(task_con)
        task_queue = self.hass.loop.create_task(self.handle_queue())
        self.tasks.append(task_queue)
        task_notif = self.hass.loop.create_task(self.madvr_client.read_notifications())
        self.tasks.append(task_notif)
        task_hb = self.hass.loop.create_task(self.madvr_client.send_heartbeat())
        self.tasks.append(task_hb)

    async def async_will_remove_from_hass(self) -> None:
        self.madvr_client.stop()
        for task in self.tasks:
            if not task.done():
                task.cancel()

    @property
    def should_poll(self):
        """Poll."""
        return True

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
        if (
            self.connection_event.is_set()
            and not self.stop_processing_commands.is_set()
        ):
            # poll anyway, but realtime notifications will also be processed immediately
            await self.async_send_command(["GetIncomingSignalInfo"])
            await self.async_send_command(["GetAspectRatio"])
            # msg dict would be cached if put below, so needs to get updated

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        # Useful for making sensors
        return self.madvr_client.msg_dict

    @property
    def is_on(self):
        """Return the last known state."""
        return self._state

    async def handle_queue(self):
        """Handle items in command queue."""
        while True:
            await self.connection_event.wait()
            # send all commands in queue
            while (
                not self.command_queue.empty()
                and not self.stop_processing_commands.is_set()
            ):
                command = await self.command_queue.get()
                _LOGGER.debug("sending queue command %s", command)
                try:
                    await self.madvr_client.send_command(command)
                except AttributeError:
                    _LOGGER.warning("issue sending command from queue")
                except Exception as err:
                    _LOGGER.error("Unexpected error when sending command: %s", err)
                finally:
                    self.command_queue.task_done()

            if self.stop_processing_commands.is_set():
                await self.clear_queue()
                _LOGGER.debug("Stopped processing commands")
                break

            await asyncio.sleep(0.1)

    async def clear_queue(self):
        """Clear all items from the command queue."""
        self.command_queue = asyncio.Queue()

    async def async_turn_off(self, **kwargs):
        """
        Send the power off command. Will tell envy to shut off and close the socket too

        send 'True' if you want standby instead
        """

        # Check if on so send_command does not open connection if its off already
        self.stop_processing_commands.set()
        await self.clear_queue()
        await self.command_queue.join()
        # power off in the background. There can be a situation where the remote is on but the thing is off then it will get stuck
        task_power = self.hass.loop.create_task(self.madvr_client.power_off())
        self.tasks.append(task_power)
        self._state = False
        _LOGGER.debug("self._state is now: %s", self._state)

        # wait until its off to start the task
        _LOGGER.debug("adding ping to hass loop")
        await asyncio.sleep(20)
        task_con = self.hass.loop.create_task(self.ping_until_alive())
        self.tasks.append(task_con)

    async def ping_until_alive(self) -> None:
        """ping unit until its alive. Once True, call open_connection"""
        cmd = f"ping -c 1 -W 2 {self.host}"
        sleep_interval = 5

        while True:
            try:
                _LOGGER.debug("Pinging with cmd %s", cmd)
                process = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                await process.communicate()

                # if ping works, turn it on and exit
                if process.returncode == 0:
                    _LOGGER.debug("ping success, turning on")
                    await asyncio.sleep(3)
                    await self.madvr_client.open_connection()
                    self._state = True

                    return

                # wait and continue
                await asyncio.sleep(sleep_interval)
                continue

            except asyncio.CancelledError as err:
                process.terminate()
                await process.wait()
                _LOGGER.error(err)
            # intentionally broad
            except Exception as err:
                _LOGGER.error("some error happened with ping: %s", err)

    async def async_turn_on(self, **kwargs):
        """
        Send the power on command but not really.
        You must call this for it to connect
        """
        # Assumes madvr is already on
        send_magic_packet(self.mac)
        await asyncio.sleep(3)
        await self.madvr_client.open_connection()
        self._state = True

    async def async_send_command(self, command: list, **kwargs):
        """Send commands to a device."""
        _LOGGER.debug("adding command %s", command)
        await self.command_queue.put(command)
