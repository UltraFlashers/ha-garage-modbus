"""Integration complete contre un faux garage Modbus RTU : vraie pile pymodbus, vraies trames."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PORT, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.garage_modbus.const import CONF_BAUDRATE, CONF_SLAVE, DOMAIN
from custom_components.garage_modbus.coordinator import decode

from .garage_simule import GarageSimule


async def test_decodage() -> None:
    d = decode([0x8000, 565, 0b1100110, 45, 3, 3, 0xFFFF, 0xFFFF, 0xFFFF])
    assert d.temperature is None and d.humidity == 56.5
    assert d.radar_distance is None and d.radar_target is None and d.battery is None
    assert d.bit(1) and d.bit(2) and d.bit(5) and d.bit(6) and not d.bit(3)
    assert decode([0xFFEC, 0, 0, 0, 0, 0, 0, 0, 15]).temperature == -2.0   # -2,0 degres, pile 15 %


@pytest.fixture
async def garage(socket_enabled):
    g = GarageSimule()
    await g.demarrer()
    g.regs(temp=250, hum=565, status=0b0000110, position=0, etat=0, cover=0, radar_d=220, radar_c=2, pile=87)
    yield g
    await g.arreter()


async def _installer(hass: HomeAssistant, garage: GarageSimule) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Garage",
        data={CONF_PORT: garage.url, CONF_BAUDRATE: 9600, CONF_SLAVE: 1},
        unique_id=f"{garage.url}_1",
    )
    entry.add_to_hass(hass)
    with patch("homeassistant.components.usb.async_setup", return_value=True):
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _relire(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


async def test_entites_et_commandes(hass: HomeAssistant, garage: GarageSimule) -> None:
    entry = await _installer(hass, garage)
    assert entry.state is ConfigEntryState.LOADED

    ent = er.async_get(hass)
    ids = {e.translation_key: e.entity_id for e in er.async_entries_for_config_entry(ent, entry.entry_id)}
    assert len(ids) == 15          # porte, lampe, stop, 7 capteurs, 5 binaires
    porte, lampe, stop = ids["porte"], ids["lampe"], ids["stop"]

    assert hass.states.get(porte).state == "closed"
    assert hass.states.get(lampe).state == "on"                     # bit 2
    assert hass.states.get(ids["presence"]).state == "on"           # bit 1
    assert hass.states.get(ids["defaut"]).state == "off"
    assert float(hass.states.get(ids["temperature"]).state) == 25.0
    assert float(hass.states.get(ids["humidite"]).state) == 56.5
    assert hass.states.get(ids["radar_cible"]).state == "immobile"
    assert hass.states.get(ids["pile_bouton"]).state == "87"
    assert hass.states.get(ids["etat_automate"]).state == "fermee"

    # Ouvrir : coil 0 = 1
    await hass.services.async_call("cover", "open_cover", {"entity_id": porte}, blocking=True)
    assert garage.coil(0) is True
    garage.regs(cover=3, position=45, etat=3)
    await _relire(hass, entry)
    assert hass.states.get(porte).state == "opening"
    assert hass.states.get(porte).attributes["current_position"] == 45

    # Fermer : coil 0 = 0 ; Stop (cover et bouton) : coil 5 = 1
    await hass.services.async_call("cover", "close_cover", {"entity_id": porte}, blocking=True)
    assert garage.coil(0) is False
    await hass.services.async_call("cover", "stop_cover", {"entity_id": porte}, blocking=True)
    assert garage.coil(5) is True
    garage.context[1].setValues(1, 5, [False])                    # la carte le fait retomber
    await hass.services.async_call("button", "press", {"entity_id": stop}, blocking=True)
    assert garage.coil(5) is True

    # Lampe : coil 1
    await hass.services.async_call("light", "turn_off", {"entity_id": lampe}, blocking=True)
    assert garage.coil(1) is False
    await hass.services.async_call("light", "turn_on", {"entity_id": lampe}, blocking=True)
    assert garage.coil(1) is True

    # Alertes : defaut, cellule, palpeur, pile faible ; sonde et radar absents
    garage.regs(status=0b1111000, temp=0x8000, radar_d=0xFFFF, radar_c=0xFFFF, pile=15)
    await _relire(hass, entry)
    for cle in ("defaut", "cellule", "palpeur", "pile_faible"):
        assert hass.states.get(ids[cle]).state == "on", cle
    assert hass.states.get(ids["temperature"]).state == STATE_UNKNOWN
    assert hass.states.get(ids["radar_distance"]).state == STATE_UNKNOWN
    assert hass.states.get(ids["pile_bouton"]).state == "15"

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_garage_injoignable(hass: HomeAssistant, socket_enabled) -> None:
    """Pas de reponse : l'entree attend et reessaie (LoRa coupe), sans planter."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_PORT: "socket://127.0.0.1:9", CONF_BAUDRATE: 9600, CONF_SLAVE: 1}
    )
    entry.add_to_hass(hass)
    with patch("homeassistant.components.usb.async_setup", return_value=True):
        await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
