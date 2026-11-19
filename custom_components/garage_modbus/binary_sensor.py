"""Capteurs binaires tires du registre 102 (etat groupe)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GarageConfigEntry
from .const import BIT_BATTERY_LOW, BIT_BEAM, BIT_FAULT, BIT_PRESENCE, BIT_SAFETY_EDGE
from .entity import GarageEntity


@dataclass(frozen=True, kw_only=True)
class GarageBinaryDescription(BinarySensorEntityDescription):
    bit: int


BINARY_SENSORS: tuple[GarageBinaryDescription, ...] = (
    GarageBinaryDescription(key="presence", device_class=BinarySensorDeviceClass.OCCUPANCY, bit=BIT_PRESENCE),
    GarageBinaryDescription(key="defaut", device_class=BinarySensorDeviceClass.PROBLEM, bit=BIT_FAULT),
    GarageBinaryDescription(key="cellule", device_class=BinarySensorDeviceClass.SAFETY, bit=BIT_BEAM),
    GarageBinaryDescription(key="palpeur", device_class=BinarySensorDeviceClass.SAFETY, bit=BIT_SAFETY_EDGE),
    GarageBinaryDescription(key="pile_faible", device_class=BinarySensorDeviceClass.BATTERY, bit=BIT_BATTERY_LOW),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: GarageConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(GarageBinarySensor(entry.runtime_data, d) for d in BINARY_SENSORS)


class GarageBinarySensor(GarageEntity, BinarySensorEntity):
    """Un bit du registre 102."""

    entity_description: GarageBinaryDescription

    def __init__(self, coordinator, description: GarageBinaryDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.bit(self.entity_description.bit)
