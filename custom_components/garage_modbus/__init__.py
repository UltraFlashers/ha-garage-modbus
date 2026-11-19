"""Garage Modbus : controleur de porte de garage ESP32-S3 (firmware v6) en Modbus RTU."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .client import GarageModbusClient
from .const import CONF_BAUDRATE, CONF_SLAVE
from .coordinator import GarageCoordinator

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.COVER,
    Platform.LIGHT,
    Platform.SENSOR,
]

type GarageConfigEntry = ConfigEntry[GarageCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: GarageConfigEntry) -> bool:
    """Ouvre la liaison et cree les entites."""
    client = GarageModbusClient(entry.data[CONF_PORT], entry.data[CONF_BAUDRATE], entry.data[CONF_SLAVE])
    coordinator = GarageCoordinator(hass, entry, client)
    try:
        # Echec = ConfigEntryNotReady : Home Assistant reessaie tout seul (LoRa coupe...)
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        client.close()
        raise
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GarageConfigEntry) -> bool:
    """Retire les entites et ferme le port serie."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry.runtime_data.client.close()
    return unloaded


async def _async_reload(hass: HomeAssistant, entry: GarageConfigEntry) -> None:
    """Options modifiees (intervalle) : rechargement."""
    await hass.config_entries.async_reload(entry.entry_id)
