"""Support for InfluxDB Sensor Platform."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, DATA_UPDATED

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the InfluxDB platform."""
    client = hass.data[DOMAIN][config_entry.entry_id]

    try:
        await hass.async_add_executor_job(client.ready)
        api = client.query_api()
    except PlatformNotReady as err:
        raise PlatformNotReady
        
    devices = [(
        'Bathroom Humidity Stvdev',
        'from(bucket: "telegraf") |> range(start: -12h) |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer" and r["_field"] == "humidity" and r["topic"] == "zigbee2mqtt/Badeværelse Luftsensor") |> stddev()',
        ''
    )]

    async_add_entities(
        [InfluxDBSensor(hass, api, *entity) for entity in devices],
        True
    )

class InfluxDBSensor(SensorEntity):
    """Device used to display information from Open Hardware Monitor."""

    def __init__(self, hass, api, name, query, unit_of_measurement):
        """Initialize an InfluxDB."""
        self.hass = hass
        self.api = api
        self._name = name
        self.query = query
        self._available = True
        self.attributes = {}
        self._unit_of_measurement = unit_of_measurement
        self.unsub_update = None

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return "_".join([DOMAIN, self._name, 'sensor'])

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._available

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def should_poll(self):
        """Return the polling requirement for this sensor."""
        return True

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

    def run_query(self):
        return self.api.query(self.query)

    async def async_update(self):
        tables = await self.hass.async_add_executor_job(self.run_query)
        self._state = tables[0].records[0].values['_value']
        _LOGGER.debug(f"Updating sensor {self._name}")
