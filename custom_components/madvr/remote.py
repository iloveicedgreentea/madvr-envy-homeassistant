"""Implement madvr component."""
from collections.abc import Iterable
import logging

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


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
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
    add_entities(
        [
            MadvrCls(name, host, madvr_client),
        ]
    )


class MadvrCls(RemoteEntity):
    """Implements the interface for Madvr Remote in HA."""

    # TODO: make second integration or secondary configuration like notification mode?
    # Based on a const, in configuration.yaml if you set notifiations = true, it wont read commands?

    # TODO: hass.async_create_task(async_say_hello(hass, target)) will that run in backgrond?
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

        # from the client
        self._incoming_res = ""
        self._incoming_frame_rate = ""
        self._incoming_color_space = ""
        self._incoming_bit_depth = ""
        self._hdr_flag = False
        self._incoming_colorimetry = ""
        self._incoming_black_levels = ""
        self._incoming_aspect_ratio = ""
        # TODO: use this to determine masking in HA
        self._aspect_ratio: float = 0

        # Temps
        self._temp_gpu: int = 0
        self._temp_hdmi: int = 0
        self._temp_cpu: int = 0
        self._temp_mainboard: int = 0

        # Outgoing signal
        self._outgoing_res = ""
        self._outgoing_frame_rate = ""
        self._outgoing_color_space = ""
        self._outgoing_bit_depth = ""
        self._outgoing_colorimetry = ""
        self._outgoing_hdr_flag = False
        self._outgoing_black_levels = ""

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

    def update(self):
        """Retrieve latest state."""
        # TODO: it should not be updating if its off

        # Should only poll if its on
        if self.is_on:
            self.madvr_client.logger.warning("Envy update is on")
            # Make the client poll, client handles heartbeat
            self.madvr_client.poll_status()

        # Add client state to entity state
        self._state = self.madvr_client.is_on

        # incoming signal
        self._incoming_res = self.madvr_client.incoming_res
        self._incoming_frame_rate = self.madvr_client.incoming_frame_rate
        self._incoming_color_space = self.madvr_client.incoming_color_space
        self._incoming_bit_depth = self.madvr_client.incoming_bit_depth
        self._hdr_flag = self.madvr_client.hdr_flag
        self._incoming_colorimetry = self.madvr_client.incoming_colorimetry
        self._incoming_black_levels = self.madvr_client.incoming_black_levels
        self._aspect_ratio = self.madvr_client.aspect_ratio

        # Temps
        self._temp_gpu: int = self.madvr_client.temp_gpu
        self._temp_hdmi: int = self.madvr_client.temp_hdmi
        self._temp_cpu: int = self.madvr_client.temp_cpu
        self._temp_mainboard: int = self.madvr_client.temp_mainboard

        # Outgoing signal
        self._outgoing_res = self.madvr_client.outgoing_res
        self._outgoing_frame_rate = self.madvr_client.outgoing_frame_rate
        self._outgoing_color_space = self.madvr_client.outgoing_color_space
        self._outgoing_bit_depth = self.madvr_client.outgoing_bit_depth
        self._outgoing_colorimetry = self.madvr_client.outgoing_colorimetry
        self._outgoing_hdr_flag = self.madvr_client.outgoing_hdr_flag
        self._outgoing_black_levels = self.madvr_client.outgoing_black_levels

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        # Useful for making sensors
        return {
            "power_state": self._state,
            "hdr_flag": self._hdr_flag,
            "incoming_resolution": self._incoming_res,
            "incoming_frame_rate": self._incoming_frame_rate,
            "incoming_color_space": self._incoming_color_space,
            "incoming_bit_depth": self._incoming_bit_depth,
            "incoming_colorimetry": self._incoming_colorimetry,
            "incoming_black_levels": self._incoming_black_levels,
            # AR
            "aspect_ratio": self._aspect_ratio,
            # temps
            "temp_gpu": self._temp_gpu,
            "temp_hdmi": self._temp_hdmi,
            "temp_cpu": self._temp_cpu,
            "temp_mainboard": self._temp_mainboard,
            # Outgoing signal
            "outgoing_res": self._outgoing_res,
            "outgoing_frame_rate": self._outgoing_frame_rate,
            "outgoing_color_space": self._outgoing_color_space,
            "outgoing_bit_depth": self._outgoing_bit_depth,
            "outgoing_colorimetry": self._outgoing_colorimetry,
            "outgoing_hdr_flag": self._outgoing_hdr_flag,
            "outgoing_black_levels": self._outgoing_black_levels,
        }

    @property
    def is_on(self):
        """Return the last known state."""
        return self._state

    def turn_off(self, standby=False):
        """
        Send the power off command. Will tell envy to shut off and close the socket too

        send 'True' if you want standby instead
        """
        self.madvr_client.close_connection()

        # Check if on so send_command does not open connection if its off already
        if self.is_on:
            self.madvr_client.power_off(standby)
            self._state = False

    def turn_on(self):
        """
        Send the power on command but not really.
        You must call this for it to connect but turn it on with IR/RF FIRST
        """
        # Assumes madvr is already on
        self.madvr_client.open_connection()
        self._state = True

    def send_command(self, command: str):
        """Send commands to a device."""

        self.madvr_client.send_command(command)
