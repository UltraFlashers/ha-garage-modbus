"""La lampe du garage."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GarageConfigEntry
from .const import BIT_LAMP, COIL_LAMP
from .entity import GarageEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: GarageConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GarageLamp(entry.runtime_data)])


class GarageLamp(GarageEntity, LightEntity):
    """Etat reel relu dans le registre 102 ; la minuterie « Home Assistant » de la carte s'applique."""

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "lampe")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.bit(BIT_LAMP)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_coil(COIL_LAMP, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_coil(COIL_LAMP, False)
