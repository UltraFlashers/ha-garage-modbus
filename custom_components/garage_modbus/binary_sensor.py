"""Capteurs binaires tires du registre 102 (etat groupe)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GarageConfigEntry
from .const import BIT_BATTERY_LOW, BIT_BEAM, BIT_FAULT, BIT_OPEN_LIMIT, BIT_PRESENCE, BIT_SAFETY_EDGE, BIT_VEHICLE, BIT_WICKET
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
    # Fin de course ouvert : « on » = porte en haut. Desactive par defaut dans Home Assistant,
    # comme sur la carte (il n'a de sens que si le contact est cable sur DI7).
    GarageBinaryDescription(
        key="fc_ouvert", bit=BIT_OPEN_LIMIT, entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False
    ),
    # Voiture garee : « on » = vehicule detecte. Simple information. Desactive par defaut,
    # comme sur la carte (il faut un capteur cable sur une DI et choisi dans les reglages).
    GarageBinaryDescription(
        key="vehicule", device_class=BinarySensorDeviceClass.OCCUPANCY, icon="mdi:car", bit=BIT_VEHICLE,
        entity_registry_enabled_default=False,
    ),
    # Portillon de la porte : « on » = ouvert, la porte est alors bloquee. Desactive par defaut,
    # comme sur la carte (contact a cabler sur une DI et a choisir dans les reglages).
    GarageBinaryDescription(
        key="portillon", device_class=BinarySensorDeviceClass.DOOR, bit=BIT_WICKET, entity_registry_enabled_default=False,
    ),
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
