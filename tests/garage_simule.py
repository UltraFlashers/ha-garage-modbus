"""Un faux garage : esclave Modbus RTU (sur TCP local) avec la carte des registres du firmware v6."""

from __future__ import annotations

import asyncio
import socket

from pymodbus import FramerType
from pymodbus.datastore import ModbusDeviceContext, ModbusSequentialDataBlock, ModbusServerContext
from pymodbus.server import ModbusTcpServer


def port_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class GarageSimule:
    """Registres 100-108 et coils 0-6, comme la carte."""

    def __init__(self) -> None:
        # Bloc commencant a 0 : pymodbus decale les adresses de 1 en interne (zero_mode absent)
        self.hr = ModbusSequentialDataBlock(0, [0] * 120)
        self.co = ModbusSequentialDataBlock(0, [False] * 16)
        ctx = ModbusDeviceContext(hr=self.hr, co=self.co)
        self.context = ModbusServerContext(devices={1: ctx}, single=False)
        self.port = port_libre()
        self.server = ModbusTcpServer(self.context, framer=FramerType.RTU, address=("127.0.0.1", self.port))
        self._task: asyncio.Task | None = None

    @property
    def url(self) -> str:
        return f"socket://127.0.0.1:{self.port}"

    def regs(self, **v: int) -> None:
        noms = ["temp", "hum", "status", "position", "etat", "cover", "radar_d", "radar_c", "pile"]
        for nom, val in v.items():
            self.context[1].setValues(3, 100 + noms.index(nom), [val])

    def coil(self, adresse: int) -> bool:
        return bool(self.context[1].getValues(1, adresse, 1)[0])

    async def demarrer(self) -> None:
        self._task = asyncio.create_task(self.server.serve_forever())
        for _ in range(50):
            await asyncio.sleep(0.02)
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                    return
            except OSError:
                pass

    async def arreter(self) -> None:
        await self.server.shutdown()
        if self._task:
            self._task.cancel()
