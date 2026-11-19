"""Lecture periodique des registres du garage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import GarageModbusClient, GarageModbusError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class GarageData:
    """Registres 100 a 108 decodes."""

    temperature: float | None
    humidity: float | None
    status: int
    position: int
    door_state: int
    cover_state: int
    radar_distance: int | None
    radar_target: int | None
    battery: int | None

    def bit(self, n: int) -> bool:
        """Bit n du registre 102."""
        return bool((self.status >> n) & 1)


def decode(regs: list[int]) -> GarageData:
    """Traduit les registres bruts (non signes) en valeurs."""

    def signed(v: int) -> int:
        return v - 0x10000 if v >= 0x8000 else v

    return GarageData(
        temperature=None if regs[0] == 0x8000 else signed(regs[0]) / 10,
        humidity=None if regs[1] == 0x8000 else signed(regs[1]) / 10,
        status=regs[2],
        position=regs[3],
        door_state=regs[4],
        cover_state=regs[5],
        radar_distance=None if regs[6] == 0xFFFF else regs[6],
        radar_target=None if regs[7] == 0xFFFF else regs[7],
        battery=None if regs[8] == 0xFFFF else regs[8],
    )


class GarageCoordinator(DataUpdateCoordinator[GarageData]):
    """Une lecture groupee par cycle, partagee par toutes les entites."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: GarageModbusClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client = client

    async def _async_update_data(self) -> GarageData:
        try:
            return decode(await self.client.read_registers())
        except GarageModbusError as err:
            raise UpdateFailed(f"Garage injoignable : {err}") from err

    async def async_write_coil(self, address: int, value: bool) -> None:
        """Envoie une commande puis relit aussitot l'etat."""
        try:
            await self.client.write_coil(address, value)
        except GarageModbusError as err:
            raise HomeAssistantError(f"Commande non transmise au garage : {err}") from err
        await self.async_request_refresh()
