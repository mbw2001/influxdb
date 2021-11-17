"""Support for InfluxDB Sensor Platform."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the InfluxDB platform."""
    client = hass.data[DOMAIN][config_entry.entry_id]

    try:
        await hass.async_add_executor_job(client.ready)
    except Exception as err:
        raise PlatformNotReady(err)

    async_add_entities([InfluxDBSensor(hass, client, *entity)
                       for entity in client.devices], True)


class InfluxDBSensor(SensorEntity):
    """Device used to display information from Open Hardware Monitor."""

    def __init__(self, hass, client, name, state, unit_of_measurement):
        """Initialize an InfluxDB."""
        self.hass = hass
        self.client = client
        self._name = name
        self._state = state
        self.attributes = {}
        self._unit_of_measurement = unit_of_measurement

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return "_".join([DOMAIN, self._name, 'sensor'])

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._state != None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def should_poll(self):
        """Return the polling requirement for this sensor."""
        return True

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the entity."""
        return self.attributes

    async def async_update(self):
        _LOGGER.debug(f"Updating sensor {self._name}")
        self.client.get_value(0)
