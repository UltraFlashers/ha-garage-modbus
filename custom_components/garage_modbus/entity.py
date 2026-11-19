"""Base commune des entites : un seul appareil « Garage »."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GarageCoordinator


class GarageEntity(CoordinatorEntity[GarageCoordinator]):
    """Entite rattachee a l'appareil Garage."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GarageCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Garage",
            manufacturer="Garage Modbus",
            model="ESP32-S3 Waveshare 8DI-8DO (firmware v6)",
        )
