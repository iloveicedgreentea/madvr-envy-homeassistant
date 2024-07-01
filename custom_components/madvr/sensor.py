"""Sensor entities for the MadVR integration."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import MadVRCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            MadvrIncomingResSensor(coordinator, entry.entry_id),
            MadvrIncomingFrameRateSensor(coordinator, entry.entry_id),
            MadvrIncomingColorSpaceSensor(coordinator, entry.entry_id),
            MadvrIncomingBitDepthSensor(coordinator, entry.entry_id),
            MadvrIncomingColorimetrySensor(coordinator, entry.entry_id),
            MadvrIncomingBlackLevelsSensor(coordinator, entry.entry_id),
            MadvrIncomingAspectRatioSensor(coordinator, entry.entry_id),
            MadvrOutgoingResSensor(coordinator, entry.entry_id),
            MadvrOutgoingFrameRateSensor(coordinator, entry.entry_id),
            MadvrOutgoingColorSpaceSensor(coordinator, entry.entry_id),
            MadvrOutgoingBitDepthSensor(coordinator, entry.entry_id),
            MadvrOutgoingColorimetrySensor(coordinator, entry.entry_id),
            MadvrOutgoingBlackLevelsSensor(coordinator, entry.entry_id),
            MadvrAspectResSensor(coordinator, entry.entry_id),
            MadvrAspectDecSensor(coordinator, entry.entry_id),
            MadvrAspectIntSensor(coordinator, entry.entry_id),
            MadvrAspectNameSensor(coordinator, entry.entry_id),
            MadvrMaskingResSensor(coordinator, entry.entry_id),
            MadvrMaskingDecSensor(coordinator, entry.entry_id),
            MadvrMaskingIntSensor(coordinator, entry.entry_id),
            MadvrProfileNameSensor(coordinator, entry.entry_id),
            MadvrProfileNumSensor(coordinator, entry.entry_id),
            MadvrMAC(coordinator, entry.entry_id),
            MadvrTempGPU(coordinator, entry.entry_id),
            MadvrTempCPU(coordinator, entry.entry_id),
            MadvrTempHDMI(coordinator, entry.entry_id),
            MadvrTempMainboard(coordinator, entry.entry_id),
        ]
    )


class MadvrBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for MadVR sensors."""

    def __init__(
        self, coordinator: MadVRCoordinator, name: str, key: str, unique_id: str
    ) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._key = key
        self._attr_unique_id = unique_id

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            val: str = self.coordinator.data.get(self._key, "")
            return val


class MadvrTempSensor(MadvrBaseSensor):
    """Base class for MadVR temperature sensors."""

    def __init__(
        self, coordinator: MadVRCoordinator, name: str, key: str, unique_id: str
    ) -> None:
        super().__init__(coordinator, name, key, unique_id)
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

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.native_value is not None


# ruff: noqa: D107
# mac
class MadvrMAC(MadvrBaseSensor):
    """Sensor for MAC."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} MAC Address",
            "mac_address",
            f"{entry_id}_mac_address",
        )
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_has_entity_name = True

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        return "mdi:ethernet"


# temps
class MadvrTempGPU(MadvrTempSensor):
    """Sensor for gpu temp."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} GPU Temperature",
            "temp_gpu",
            f"{entry_id}_temp_gpu",
        )


class MadvrTempHDMI(MadvrTempSensor):
    """Sensor for hdmi temp."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} HDMI Temperature",
            "temp_hdmi",
            f"{entry_id}_temp_hdmi",
        )


class MadvrTempCPU(MadvrTempSensor):
    """Sensor for CPU temp."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} CPU Temperature",
            "temp_cpu",
            f"{entry_id}_temp_cpu",
        )


class MadvrTempMainboard(MadvrTempSensor):
    """Sensor for mainboard temp."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Mainboard Temperature",
            "temp_mainboard",
            f"{entry_id}_temp_mainboard",
        )


class MadvrIncomingResSensor(MadvrBaseSensor):
    """Sensor for incoming resolution."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Resolution",
            "incoming_res",
            f"{entry_id}_incoming_res",
        )


class MadvrIncomingFrameRateSensor(MadvrBaseSensor):
    """Sensor for incoming frame rate."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Frame Rate",
            "incoming_frame_rate",
            f"{entry_id}_incoming_frame_rate",
        )


class MadvrIncomingColorSpaceSensor(MadvrBaseSensor):
    """Sensor for incoming color space."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Color Space",
            "incoming_color_space",
            f"{entry_id}_incoming_color_space",
        )


class MadvrIncomingBitDepthSensor(MadvrBaseSensor):
    """Sensor for incoming bit depth."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Bit Depth",
            "incoming_bit_depth",
            f"{entry_id}_incoming_bit_depth",
        )


class MadvrIncomingColorimetrySensor(MadvrBaseSensor):
    """Sensor for incoming colorimetry."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Colorimetry",
            "incoming_colorimetry",
            f"{entry_id}_incoming_colorimetry",
        )


class MadvrIncomingBlackLevelsSensor(MadvrBaseSensor):
    """Sensor for incoming black levels."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Black Levels",
            "incoming_black_levels",
            f"{entry_id}_incoming_black_levels",
        )


class MadvrIncomingAspectRatioSensor(MadvrBaseSensor):
    """Sensor for incoming aspect ratio."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Incoming Aspect Ratio",
            "incoming_aspect_ratio",
            f"{entry_id}_incoming_aspect_ratio",
        )


class MadvrOutgoingResSensor(MadvrBaseSensor):
    """Sensor for outgoing resolution."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Resolution",
            "outgoing_res",
            f"{entry_id}_outgoing_res",
        )


class MadvrOutgoingFrameRateSensor(MadvrBaseSensor):
    """Sensor for outgoing frame rate."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Frame Rate",
            "outgoing_frame_rate",
            f"{entry_id}_outgoing_frame_rate",
        )


class MadvrOutgoingColorSpaceSensor(MadvrBaseSensor):
    """Sensor for outgoing color space."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Color Space",
            "outgoing_color_space",
            f"{entry_id}_outgoing_color_space",
        )


class MadvrOutgoingBitDepthSensor(MadvrBaseSensor):
    """Sensor for outgoing bit depth."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Bit Depth",
            "outgoing_bit_depth",
            f"{entry_id}_outgoing_bit_depth",
        )


class MadvrOutgoingColorimetrySensor(MadvrBaseSensor):
    """Sensor for outgoing colorimetry."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Colorimetry",
            "outgoing_colorimetry",
            f"{entry_id}_outgoing_colorimetry",
        )


class MadvrOutgoingBlackLevelsSensor(MadvrBaseSensor):
    """Sensor for outgoing black levels."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Outgoing Black Levels",
            "outgoing_black_levels",
            f"{entry_id}_outgoing_black_levels",
        )


class MadvrAspectResSensor(MadvrBaseSensor):
    """Sensor for aspect ratio resolution."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Aspect Ratio Resolution",
            "aspect_res",
            f"{entry_id}_aspect_res",
        )


class MadvrAspectDecSensor(MadvrBaseSensor):
    """Sensor for aspect ratio decimal value."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Aspect Ratio Decimal",
            "aspect_dec",
            f"{entry_id}_aspect_dec",
        )


class MadvrAspectIntSensor(MadvrBaseSensor):
    """Sensor for aspect ratio integer value."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Aspect Ratio Integer",
            "aspect_int",
            f"{entry_id}_aspect_int",
        )


class MadvrAspectNameSensor(MadvrBaseSensor):
    """Sensor for aspect ratio name."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Aspect Ratio Name",
            "aspect_name",
            f"{entry_id}_aspect_name",
        )


class MadvrMaskingResSensor(MadvrBaseSensor):
    """Sensor for masking resolution."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Masking Resolution",
            "masking_res",
            f"{entry_id}_masking_res",
        )


class MadvrMaskingDecSensor(MadvrBaseSensor):
    """Sensor for masking decimal value."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Masking Decimal",
            "masking_dec",
            f"{entry_id}_masking_dec",
        )


class MadvrMaskingIntSensor(MadvrBaseSensor):
    """Sensor for masking integer value."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Masking Integer",
            "masking_int",
            f"{entry_id}_masking_int",
        )


class MadvrProfileNameSensor(MadvrBaseSensor):
    """Sensor for profile name."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Profile Name",
            "profile_name",
            f"{entry_id}_profile_name",
        )


class MadvrProfileNumSensor(MadvrBaseSensor):
    """Sensor for profile number."""

    def __init__(self, coordinator: MadVRCoordinator, entry_id: str) -> None:
        super().__init__(
            coordinator,
            f"{coordinator.name} Profile Number",
            "profile_num",
            f"{entry_id}_profile_num",
        )
