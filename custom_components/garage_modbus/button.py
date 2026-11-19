"""Bouton Stop."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GarageConfigEntry
from .const import COIL_STOP
from .entity import GarageEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: GarageConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GarageStop(entry.runtime_data)])


class GarageStop(GarageEntity, ButtonEntity):
    """Arrete la porte immediatement, quelle que soit l'origine du mouvement."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "stop")

    async def async_press(self) -> None:
        await self.coordinator.async_write_coil(COIL_STOP, True)
