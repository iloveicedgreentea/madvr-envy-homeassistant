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
        self._state = self.madvr_client.is_on
        self._incoming_res = ""
        self._incoming_frame_rate = ""
        self._incoming_color_space = ""
        self._incoming_bit_depth = ""
        self._hdr_flag = False
        self._incoming_colorimetry = ""
        self._incoming_black_levels = ""
        # TODO: use this to determine masking in HA
        self._aspect_ratio: float = 0

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
            "aspect_ratio": self._aspect_ratio
        }

    @property
    def is_on(self):
        """Return the last known state of the projector."""
        return self._state

     # TODO: HA should close client on shutdown
    # TODO opene oconnection on startup

    # Can't implement right now because of their API not working when off
    # TODO: maybe do wake on lan here
    # def turn_on(self, **kwargs):
    #     """Send the power on command."""

    #     self.madvr_client.power_on()
    #     self._state = True

    def turn_off(self, **kwargs):
        """Send the power off command."""
        self.madvr_client.power_off()
        self._state = False

    def turn_on(self, **kwargs):
        """Send the power on command but not really."""
        # Assumes madvr is already on
        self.madvr_client.open_connection()
        self._state = True

    def send_command(self, command: str):
        """Send commands to a device."""

        self.madvr_client.send_command(command)
