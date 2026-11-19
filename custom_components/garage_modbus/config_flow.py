"""Configuration par l'interface : choix du port USB dans une liste, vitesse, esclave."""

from __future__ import annotations

import asyncio
from typing import Any

import serial.tools.list_ports
import voluptuous as vol

from homeassistant.components import usb
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .client import GarageModbusClient, GarageModbusError
from .const import (
    BAUDRATES,
    CONF_BAUDRATE,
    CONF_MANUAL_PATH,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE,
    DEFAULT_BAUDRATE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DOMAIN,
)

MANUAL = "manual"


def _list_ports() -> dict[str, str]:
    """Ports serie presents : chemin stable /dev/serial/by-id -> libelle lisible."""
    ports: dict[str, str] = {}
    for p in serial.tools.list_ports.comports():
        path = usb.get_serial_by_id(p.device)
        ports[path] = usb.human_readable_device_name(
            p.device, p.serial_number, p.manufacturer, p.description, p.vid, p.pid
        )
    return ports


async def _test_connection(port: str, baudrate: int, slave: int) -> None:
    """Une lecture des registres 100-108 : le garage doit repondre."""
    client = GarageModbusClient(port, baudrate, slave)
    try:
        await asyncio.wait_for(client.read_registers(), timeout=20)
    except TimeoutError as err:
        raise GarageModbusError("pas de reponse") from err
    finally:
        client.close()


def _schema(ports: dict[str, str], defaults: dict[str, Any]) -> vol.Schema:
    options = [SelectOptionDict(value=path, label=label) for path, label in ports.items()]
    options.append(SelectOptionDict(value=MANUAL, label="manual"))
    default_port = defaults.get(CONF_PORT)
    if default_port not in ports:
        default_port = next(iter(ports), MANUAL) if default_port is None else MANUAL
    return vol.Schema(
        {
            vol.Required(CONF_PORT, default=default_port): SelectSelector(
                SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST, translation_key="port")
            ),
            vol.Required(CONF_BAUDRATE, default=str(defaults.get(CONF_BAUDRATE, DEFAULT_BAUDRATE))): SelectSelector(
                SelectSelectorConfig(options=[str(b) for b in BAUDRATES], mode=SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(CONF_SLAVE, default=defaults.get(CONF_SLAVE, DEFAULT_SLAVE)): NumberSelector(
                NumberSelectorConfig(min=1, max=247, step=1, mode=NumberSelectorMode.BOX)
            ),
        }
    )


class GarageModbusConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ajout du garage : port USB, vitesse, numero d'esclave."""

    VERSION = 1

    def __init__(self) -> None:
        self._settings: dict[str, Any] = {}

    async def _ports(self) -> dict[str, str]:
        return await self.hass.async_add_executor_job(_list_ports)

    async def _finish(self, data: dict[str, Any], errors: dict[str, str]) -> ConfigFlowResult | None:
        """Teste la liaison puis cree (ou met a jour) l'entree. None si echec."""
        if self.source == "reconfigure":
            # Pas de test : l'integration en service tient le port serie ouvert (acces exclusif).
            # Si le nouveau reglage ne repond pas, l'entree passe en « nouvel essai » toute seule.
            entry = self._get_reconfigure_entry()
            return self.async_update_reload_and_abort(entry, data=data)
        try:
            await _test_connection(data[CONF_PORT], data[CONF_BAUDRATE], data[CONF_SLAVE])
        except GarageModbusError:
            errors["base"] = "cannot_connect"
            return None
        await self.async_set_unique_id(f"{data[CONF_PORT]}_{data[CONF_SLAVE]}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Garage", data=data)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._step_port("user", user_input, {})

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Changer de port USB, de vitesse ou d'esclave plus tard."""
        return await self._step_port("reconfigure", user_input, dict(self._get_reconfigure_entry().data))

    async def _step_port(
        self, step_id: str, user_input: dict[str, Any] | None, defaults: dict[str, Any]
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        ports = await self._ports()
        if user_input is not None:
            self._settings = {
                CONF_PORT: user_input[CONF_PORT],
                CONF_BAUDRATE: int(user_input[CONF_BAUDRATE]),
                CONF_SLAVE: int(user_input[CONF_SLAVE]),
            }
            if user_input[CONF_PORT] == MANUAL:
                return await self.async_step_manual()
            if result := await self._finish(self._settings, errors):
                return result
            defaults = self._settings
        return self.async_show_form(step_id=step_id, data_schema=_schema(ports, defaults), errors=errors)

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Chemin saisi a la main (port non liste, ou passerelle serie)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._settings[CONF_PORT] = user_input[CONF_MANUAL_PATH].strip()
            if result := await self._finish(self._settings, errors):
                return result
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {vol.Required(CONF_MANUAL_PATH, default="/dev/serial/by-id/"): str}
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return GarageModbusOptionsFlow()


class GarageModbusOptionsFlow(OptionsFlow):
    """Intervalle de lecture."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])})
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): NumberSelector(
                        NumberSelectorConfig(
                            min=2, max=300, step=1, unit_of_measurement="s", mode=NumberSelectorMode.BOX
                        )
                    )
                }
            ),
        )
