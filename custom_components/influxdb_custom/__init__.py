""" Custom InfluxDB component """
import logging

from homeassistant.config_entries import ConfigEntry, ConfigType, SOURCE_IMPORT
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SSL, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN, CONF_QUERY, CONF_ORG

from influxdb_client import InfluxDBClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configure InfluxDB using config flow only."""
    if DOMAIN in config:
        for entry in config[DOMAIN]:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}, data=entry
                )
            )
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Configure InfluxDB from config entry."""
    try:
        url = f"http{'s' if config_entry.data[CONF_SSL] else ''}://{config_entry.data[CONF_HOST]}:{config_entry.data[CONF_PORT]}"

        client = CustomInfluxDBClient(
            hass=hass,
            url=url,
            token=config_entry.data[CONF_TOKEN],
            org=config_entry.data[CONF_ORG],
            query=config_entry.data[CONF_QUERY])

        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = client
        hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)

        return True

    except Exception as err:
        _LOGGER.debug("Can not connect to InfluxDB")
        raise ConfigEntryNotReady from err


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload InfluxDB config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok


class CustomInfluxDBClient(InfluxDBClient):
    def __init__(self, hass: HomeAssistant, url: str, token: str, org: str, query: str):
        super().__init__(url=url, token=token, org=org)
        self.hass = hass
        self.api = self.query_api()
        self.query = query
        _LOGGER.debug(f"Running query: {self.query}")
        self.async_update()
        self.devices = [('Test', 1, '')]

    async def get_value(self, i: int):
        _LOGGER.debug(f"Getting value for: {i}")
        return self.devices[i][1]

    def update(self):
        _LOGGER.debug(f"Running query: {self.query}")
        tables = self.api.query(self.query)
        self.devices = [(
            tables[0].records[0].values['result'],
            tables[0].records[0].values['_value'],
            ''
        )]

    async def async_update(self):
        _LOGGER.debug(f"Running query: {self.query}")
        return await self.hass.async_add_executor_job(self.update)
