"""Implement madvr component."""
from collections.abc import Iterable
import logging

from madvr.madvr import Madvr
import voluptuous as vol

from homeassistant.components.remote import PLATFORM_SCHEMA, RemoteEntity
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_TIMEOUT
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
        vol.Optional(CONF_PASSWORD): cv.string,
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
    password = config.get(CONF_PASSWORD)
    madvr_client = Madvr(
        host=host,
        password=password,
        logger=_LOGGER,
        connect_timeout=config.get(CONF_TIMEOUT),
    )
    # create a long lived connection
    # TODO: its going to fail unless on
    madvr_client.open_connection()
    add_entities(
        [
            Madvr(name, host, madvr_client),
        ]
    )

class MadVR(RemoteEntity):
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
        self.madvr_client = madvr_client

    @property
    def should_poll(self):
        """Poll."""
#       
        return True

    @property
    def name(self):
        """Name."""
        return self._name

    @property
    def host(self):
        """Host."""
        return self._host

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        # Useful for making sensors
        return {
            "power_state": self._state,
        }

    @property
    def is_on(self):
        """Return the last known state of the projector."""

        return self._state

    # Can't implement right now because of their API not working when off
    # TODO: maybe do wake on lan here
    # def turn_on(self, **kwargs):
    #     """Send the power on command."""

    #     self.madvr_client.power_on()
    #     self._state = True

    def turn_off(self, **kwargs):
        """Send the power off command."""

        self.madvr_client.send_command("power_off")
        self._state = False

    def update(self):
        """Retrieve latest state."""
        # TODO: press power and then green with a small delay to turn it off
        pass
        # TODO: is there way to poll for power state
        # self._state = self.madvr_client.is_on()

    def send_command(self, command: str, **kwargs):
        """Send commands to a device."""

        self.madvr_client.send_command(command)
