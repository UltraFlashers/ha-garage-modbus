"""Acces Modbus RTU au controleur de garage (adaptateur USB-RS485)."""

from __future__ import annotations

import asyncio
import inspect

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from .const import DEFAULT_TIMEOUT, REG_COUNT, REG_FIRST


class GarageModbusError(Exception):
    """La carte ne repond pas ou repond par une erreur."""


class GarageModbusClient:
    """Une seule liaison serie, une requete a la fois (bus RS485 en semi-duplex)."""

    def __init__(self, port: str, baudrate: int, slave: int, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._client = AsyncModbusSerialClient(
            port,
            baudrate=baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=timeout,
            retries=1,
        )
        self._slave = slave
        self._lock = asyncio.Lock()
        # pymodbus >= 3.9 : device_id ; versions plus anciennes : slave
        params = inspect.signature(self._client.read_holding_registers).parameters
        self._unit_kw = "device_id" if "device_id" in params else "slave"

    async def _connect(self) -> None:
        if not self._client.connected and not await self._client.connect():
            raise GarageModbusError("port serie inaccessible")

    async def read_registers(self) -> list[int]:
        """Lit les registres 100 a 108 en une seule requete."""
        async with self._lock:
            await self._connect()
            try:
                result = await self._client.read_holding_registers(
                    REG_FIRST, count=REG_COUNT, **{self._unit_kw: self._slave}
                )
            except ModbusException as err:
                raise GarageModbusError(str(err)) from err
            if result.isError() or len(result.registers) < REG_COUNT:
                raise GarageModbusError(f"reponse invalide : {result}")
            return list(result.registers)

    async def write_coil(self, address: int, value: bool) -> None:
        """Ecrit une commande (coil)."""
        async with self._lock:
            await self._connect()
            try:
                result = await self._client.write_coil(address, value, **{self._unit_kw: self._slave})
            except ModbusException as err:
                raise GarageModbusError(str(err)) from err
            if result.isError():
                raise GarageModbusError(f"ecriture refusee : {result}")

    def close(self) -> None:
        """Ferme le port serie."""
        self._client.close()
