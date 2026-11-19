"""Assistant d'ajout : liste des ports USB, saisie manuelle, garage muet, doublon, reconfiguration."""

from __future__ import annotations

from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.garage_modbus.client import GarageModbusError
from custom_components.garage_modbus.const import CONF_BAUDRATE, CONF_MANUAL_PATH, CONF_SCAN_INTERVAL, CONF_SLAVE, DOMAIN

PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
PORTS = {PORT: "USB Serial - /dev/ttyUSB0, s/n: n/a - QinHeng - 1A86:7523"}
CF = "custom_components.garage_modbus.config_flow"


async def test_choix_dans_la_liste(hass: HomeAssistant) -> None:
    with patch(f"{CF}._list_ports", return_value=PORTS):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "user"
    # le menu propose le port detecte et la saisie manuelle
    options = result["data_schema"].schema[CONF_PORT].config["options"]
    assert [o["value"] for o in options] == [PORT, "manual"]

    with patch(f"{CF}._list_ports", return_value=PORTS), patch(f"{CF}._test_connection") as test, patch(
        "custom_components.garage_modbus.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PORT: PORT, CONF_BAUDRATE: "9600", CONF_SLAVE: 1.0}
        )
    test.assert_called_once_with(PORT, 9600, 1)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_PORT: PORT, CONF_BAUDRATE: 9600, CONF_SLAVE: 1}


async def test_garage_muet_puis_ok(hass: HomeAssistant) -> None:
    with patch(f"{CF}._list_ports", return_value=PORTS):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch(f"{CF}._list_ports", return_value=PORTS), patch(f"{CF}._test_connection", side_effect=GarageModbusError):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PORT: PORT, CONF_BAUDRATE: "19200", CONF_SLAVE: 3}
        )
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": "cannot_connect"}


async def test_saisie_manuelle(hass: HomeAssistant) -> None:
    with patch(f"{CF}._list_ports", return_value={}):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        assert [o["value"] for o in result["data_schema"].schema[CONF_PORT].config["options"]] == ["manual"]
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PORT: "manual", CONF_BAUDRATE: "9600", CONF_SLAVE: 1}
        )
    assert result["step_id"] == "manual"
    with patch(f"{CF}._test_connection"), patch("custom_components.garage_modbus.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_MANUAL_PATH: " /dev/ttyACM0 "})
    assert result["type"] is FlowResultType.CREATE_ENTRY and result["data"][CONF_PORT] == "/dev/ttyACM0"


async def test_doublon(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=f"{PORT}_1", data={CONF_PORT: PORT, CONF_BAUDRATE: 9600, CONF_SLAVE: 1}).add_to_hass(hass)
    with patch(f"{CF}._list_ports", return_value=PORTS):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch(f"{CF}._list_ports", return_value=PORTS), patch(f"{CF}._test_connection"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PORT: PORT, CONF_BAUDRATE: "9600", CONF_SLAVE: 1}
        )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "already_configured"


async def test_reconfiguration_et_options(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=f"{PORT}_1", data={CONF_PORT: PORT, CONF_BAUDRATE: 9600, CONF_SLAVE: 1})
    entry.add_to_hass(hass)
    autre = "/dev/serial/by-id/usb-FTDI-port0"
    with patch(f"{CF}._list_ports", return_value={**PORTS, autre: "FTDI"}):
        result = await entry.start_reconfigure_flow(hass)
        assert result["step_id"] == "reconfigure"
        with patch("custom_components.garage_modbus.async_setup_entry", return_value=True):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_PORT: autre, CONF_BAUDRATE: "115200", CONF_SLAVE: 2}
            )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    assert entry.data == {CONF_PORT: autre, CONF_BAUDRATE: 115200, CONF_SLAVE: 2}

    with patch("custom_components.garage_modbus.async_setup_entry", return_value=True):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(result["flow_id"], {CONF_SCAN_INTERVAL: 10.0})
    assert result["type"] is FlowResultType.CREATE_ENTRY and entry.options == {CONF_SCAN_INTERVAL: 10}
