"""Config flow to configure InfluxDB."""
import logging

import voluptuous as vol
from influxdb_client import InfluxDBClient

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SSL, CONF_TOKEN, CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import callback

from .const import DOMAIN, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_SSL, DEFAULT_NAME, DEFAULT_QUERY, DEFAULT_SCAN_INTERVAL, CONF_ORG, CONF_QUERY

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        vol.Required(CONF_SSL, default=DEFAULT_SSL): bool,
        vol.Required(CONF_TOKEN): str,
        vol.Required(CONF_ORG): str,
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_QUERY, default=DEFAULT_QUERY): str
    }
)


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
            self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})

            """Validate the user input allows us to connect."""
            url = f"http{'s' if user_input[CONF_SSL] else ''}://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            token = user_input[CONF_TOKEN]
            org = user_input[CONF_ORG]
            
            try:
                client = InfluxDBClient(
                    url=url, token=token, org=org)
                await self.hass.async_add_executor_job(client.ready)
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input
                )
            except Exception as e:
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
