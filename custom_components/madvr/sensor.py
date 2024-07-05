"""Sensor entities for the MadVR integration."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature


from .const import DOMAIN
from .coordinator import MadVRCoordinator

type MadVRConfigEntry = ConfigEntry[MadVRCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MadVRConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities."""
    coordinator: MadVRCoordinator = entry.runtime_data
    async_add_entities(
        [
            MadvrIncomingResSensor(coordinator),
            MadvrIncomingFrameRateSensor(coordinator),
            MadvrIncomingColorSpaceSensor(coordinator),
            MadvrIncomingBitDepthSensor(coordinator),
            MadvrIncomingColorimetrySensor(coordinator),
            MadvrIncomingBlackLevelsSensor(coordinator),
            MadvrIncomingAspectRatioSensor(coordinator),
            MadvrOutgoingResSensor(coordinator),
            MadvrOutgoingFrameRateSensor(coordinator),
            MadvrOutgoingColorSpaceSensor(coordinator),
            MadvrOutgoingBitDepthSensor(coordinator),
            MadvrOutgoingColorimetrySensor(coordinator),
            MadvrOutgoingBlackLevelsSensor(coordinator),
            MadvrAspectResSensor(coordinator),
            MadvrAspectDecSensor(coordinator),
            MadvrAspectIntSensor(coordinator),
            MadvrAspectNameSensor(coordinator),
            MadvrMaskingResSensor(coordinator),
            MadvrMaskingDecSensor(coordinator),
            MadvrMaskingIntSensor(coordinator),
            MadvrProfileNameSensor(coordinator),
            MadvrProfileNumSensor(coordinator),
            MadvrMAC(coordinator),
            MadvrTempGPU(coordinator),
            MadvrTempCPU(coordinator),
            MadvrTempHDMI(coordinator),
            MadvrTempMainboard(coordinator),
        ]
    )


class MadvrBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for MadVR sensors."""

    _attr_has_entity_name = True
    coordinator: MadVRCoordinator

    def __init__(self, coordinator: MadVRCoordinator, name: str, key: str) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._key = key
        self._attr_unique_id = f"{coordinator.mac}_{key}"

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
            name="madVR Envy",
            manufacturer="madVR",
            model="Envy",
        )

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self._key)
        return None


# ruff: noqa: D107
class MadvrTempSensor(MadvrBaseSensor):
    """Base class for MadVR temperature sensors."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: MadVRCoordinator, name: str, key: str) -> None:
        super().__init__(coordinator, name, key)
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            temp = self.coordinator.data.get(self._key)
            if temp is not None:
                try:
                    return float(temp)
                except ValueError:
                    return None
        return None


class MadvrMAC(MadvrBaseSensor):
    """Sensor for MAC."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} MAC Address",
            "mac_address",
        )
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        return "mdi:ethernet"


class MadvrTempGPU(MadvrTempSensor):
    """Sensor for gpu temp."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} GPU Temperature",
            "temp_gpu",
        )


class MadvrTempHDMI(MadvrTempSensor):
    """Sensor for hdmi temp."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} HDMI Temperature",
            "temp_hdmi",
        )


class MadvrTempCPU(MadvrTempSensor):
    """Sensor for CPU temp."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} CPU Temperature",
            "temp_cpu",
        )


class MadvrTempMainboard(MadvrTempSensor):
    """Sensor for mainboard temp."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Mainboard Temperature",
            "temp_mainboard",
        )


class MadvrIncomingResSensor(MadvrBaseSensor):
    """Sensor for incoming resolution."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Resolution",
            "incoming_res",
        )


class MadvrIncomingFrameRateSensor(MadvrBaseSensor):
    """Sensor for incoming frame rate."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Frame Rate",
            "incoming_frame_rate",
        )


class MadvrIncomingColorSpaceSensor(MadvrBaseSensor):
    """Sensor for incoming color space."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Color Space",
            "incoming_color_space",
        )


class MadvrIncomingBitDepthSensor(MadvrBaseSensor):
    """Sensor for incoming bit depth."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Bit Depth",
            "incoming_bit_depth",
        )


class MadvrIncomingColorimetrySensor(MadvrBaseSensor):
    """Sensor for incoming colorimetry."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Colorimetry",
            "incoming_colorimetry",
        )


class MadvrIncomingBlackLevelsSensor(MadvrBaseSensor):
    """Sensor for incoming black levels."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Black Levels",
            "incoming_black_levels",
        )


class MadvrIncomingAspectRatioSensor(MadvrBaseSensor):
    """Sensor for incoming aspect ratio."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Aspect Ratio",
            "incoming_aspect_ratio",
        )


class MadvrOutgoingResSensor(MadvrBaseSensor):
    """Sensor for outgoing resolution."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Resolution",
            "outgoing_res",
        )


class MadvrOutgoingFrameRateSensor(MadvrBaseSensor):
    """Sensor for outgoing frame rate."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Frame Rate",
            "outgoing_frame_rate",
        )


class MadvrOutgoingColorSpaceSensor(MadvrBaseSensor):
    """Sensor for outgoing color space."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Color Space",
            "outgoing_color_space",
        )


class MadvrOutgoingBitDepthSensor(MadvrBaseSensor):
    """Sensor for outgoing bit depth."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Bit Depth",
            "outgoing_bit_depth",
        )


class MadvrOutgoingColorimetrySensor(MadvrBaseSensor):
    """Sensor for outgoing colorimetry."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Colorimetry",
            "outgoing_colorimetry",
        )


class MadvrOutgoingBlackLevelsSensor(MadvrBaseSensor):
    """Sensor for outgoing black levels."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Black Levels",
            "outgoing_black_levels",
        )


class MadvrAspectResSensor(MadvrBaseSensor):
    """Sensor for aspect ratio resolution."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Aspect Ratio Resolution",
            "aspect_res",
        )


class MadvrAspectDecSensor(MadvrBaseSensor):
    """Sensor for aspect ratio decimal value."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Aspect Ratio Decimal",
            "aspect_dec",
        )


class MadvrAspectIntSensor(MadvrBaseSensor):
    """Sensor for aspect ratio integer value."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Aspect Ratio Integer",
            "aspect_int",
        )


class MadvrAspectNameSensor(MadvrBaseSensor):
    """Sensor for aspect ratio name."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Aspect Ratio Name",
            "aspect_name",
        )


class MadvrMaskingResSensor(MadvrBaseSensor):
    """Sensor for masking resolution."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Masking Resolution",
            "masking_res",
        )


class MadvrMaskingDecSensor(MadvrBaseSensor):
    """Sensor for masking decimal value."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Masking Decimal",
            "masking_dec",
        )


class MadvrMaskingIntSensor(MadvrBaseSensor):
    """Sensor for masking integer value."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Masking Integer",
            "masking_int",
        )


class MadvrProfileNameSensor(MadvrBaseSensor):
    """Sensor for profile name."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Profile Name",
            "profile_name",
        )


class MadvrProfileNumSensor(MadvrBaseSensor):
    """Sensor for profile number."""

    def __init__(self, coordinator: MadVRCoordinator) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Profile Number",
            "profile_num",
        )
