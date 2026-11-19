"""La porte de garage."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GarageConfigEntry
from .const import COIL_DOOR, COIL_STOP, COVER_CLOSED, COVER_CLOSING, COVER_OPENING
from .entity import GarageEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: GarageConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GarageDoor(entry.runtime_data)])


class GarageDoor(GarageEntity, CoverEntity):
    """Ouvrir / fermer / stop ; la carte applique ses securites (cellule, palpeur, STOP)."""

    _attr_device_class = CoverDeviceClass.GARAGE
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "porte")

    @property
    def is_closed(self) -> bool:
        return self.coordinator.data.cover_state == COVER_CLOSED

    @property
    def is_opening(self) -> bool:
        return self.coordinator.data.cover_state == COVER_OPENING

    @property
    def is_closing(self) -> bool:
        return self.coordinator.data.cover_state == COVER_CLOSING

    @property
    def current_cover_position(self) -> int:
        """Position estimee par la carte (seul le fin de course ferme la recale)."""
        return self.coordinator.data.position

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_coil(COIL_DOOR, True)

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_coil(COIL_DOOR, False)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_coil(COIL_STOP, True)
