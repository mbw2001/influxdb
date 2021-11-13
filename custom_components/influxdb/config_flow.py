"""Config flow to configure InfluxDB."""

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int)
    }
)

async def validate_input(hass: HomeAssistant, user_input):
    """Validate the user input allows us to connect."""
    try:
        return True
    except HomeAssistantError as err:
        raise CannotConnect from err

class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle an InfluxDB config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
    
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})

            try:
                name = await validate_input(self.hass, user_input)
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
        
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

class OptionsFlowHandler(OptionsFlow):
    """Handle InfluxDB options."""

    def __init__(self, config_entry):
        """Initialize InfluxDB options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the InfluxDB options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): int
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
