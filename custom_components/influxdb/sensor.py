"""Support for InfluxDB Sensor Platform."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the InfluxDB platform."""
    client = hass.data[DOMAIN][config_entry.entry_id]

    if client.data is None:
        raise PlatformNotReady

    async_add_entities(
        [InfluxDBSensor(*entity) for entity in client.devices],
        True
    )

class InfluxDBSensor(SensorEntity):
    """Device used to display information from Open Hardware Monitor."""

    def __init__(self, client, child_names, path, unit_of_measurement):
        """Initialize an InfluxDB."""
        self.client = client
        self.child_names = child_names
        self._name = " ".join(child_names)
        self.path = path
        self.attributes = {}
        self._unit_of_measurement = unit_of_measurement
        self._state = None
        self.unsub_update = None

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return "_".join(
            [
                DOMAIN,
                self._name,
                self._unit_of_measurement,
                "sensor"
            ]
        )

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self.client.available

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def should_poll(self):
        """Return the polling requirement for this sensor."""
        return False

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        self.unsub_update = async_dispatcher_connect(
            self.hass, DATA_UPDATED, self._schedule_immediate_update
        )

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)

    async def will_remove_from_hass(self):
        """Unsubscribe from update dispatcher."""
        if self.unsub_update:
            self.unsub_update()
        self.unsub_update = None

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

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Open Hardware Monitor instance."""
        return {
            "identifiers": {
                (DOMAIN, self.child_names[0], self.child_names[1])
            },
            "name": self.child_names[1],
            "manufacturer": self.child_names[1].split(" ", 1)[0],
            "model": self.child_names[1].split(" ", 1)[1]
        }

    async def async_update(self):
      return
