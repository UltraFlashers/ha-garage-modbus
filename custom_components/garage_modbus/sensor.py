"""Capteurs : temperature, humidite, position, radar, pile du bouton, etat de l'automate."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfLength, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GarageConfigEntry
from .const import DOOR_STATES, RADAR_TARGETS
from .coordinator import GarageData
from .entity import GarageEntity


def _enum(values: list[str], index: int | None) -> str | None:
    return values[index] if index is not None and 0 <= index < len(values) else None


@dataclass(frozen=True, kw_only=True)
class GarageSensorDescription(SensorEntityDescription):
    value_fn: Callable[[GarageData], float | int | str | None]


SENSORS: tuple[GarageSensorDescription, ...] = (
    GarageSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda d: d.temperature,
    ),
    GarageSensorDescription(
        key="humidite",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda d: d.humidity,
    ),
    GarageSensorDescription(
        key="position",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: d.position,
    ),
    GarageSensorDescription(
        key="radar_distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        value_fn=lambda d: d.radar_distance,
    ),
    GarageSensorDescription(
        key="radar_cible",
        device_class=SensorDeviceClass.ENUM,
        options=RADAR_TARGETS,
        value_fn=lambda d: _enum(RADAR_TARGETS, d.radar_target),
    ),
    GarageSensorDescription(
        key="pile_bouton",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: d.battery,
    ),
    GarageSensorDescription(
        key="etat_automate",
        device_class=SensorDeviceClass.ENUM,
        options=DOOR_STATES,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _enum(DOOR_STATES, d.door_state),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: GarageConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(GarageSensor(entry.runtime_data, d) for d in SENSORS)


class GarageSensor(GarageEntity, SensorEntity):
    """Valeur tiree de la derniere lecture groupee."""

    entity_description: GarageSensorDescription

    def __init__(self, coordinator, description: GarageSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | int | str | None:
        return self.entity_description.value_fn(self.coordinator.data)
