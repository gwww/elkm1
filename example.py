from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity

import asyncio
import elkm1
import logging
from elkm1.const import ZoneType, ZoneLogicalStatus
from elkm1.proto import Connection
from homeassistant.core import callback

REQUIREMENTS = ['elkm1==0.0.1']

_LOGGER = logging.getLogger(__name__)

@asyncio.coroutine
def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    elk = elkm1.Elk({}, loop=hass.loop)

    @asyncio.coroutine
    def connect():
        _LOGGER.debug("Elk connect")
        yield from elk.connect(url='elk://192.168.1.142')

    hass.async_add_job(connect)

    ha_zones = []
    for zone in elk.zones:
        _LOGGER.debug("Adding zone '%s'", zone.name)
        ha_zones.append(Zone(zone))
    add_devices(ha_zones)

class Zone(Entity):
    """Representation of a Sensor."""

    def __init__(self, zone):
        """Initialize the sensor."""
        self._zone = zone
        self._zone.add_callback(self.trigger_update)
        self._state = None
        self._hidden = True

    @property
    def should_poll(self):
        """No polling required."""
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._zone.name

    @property
    def hidden(self):
        """Return the name of the sensor."""
        return self._hidden

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @callback
    def trigger_update(self):
        """Target of TestHomeAutomation callback."""
        self.async_schedule_update_ha_state(True)

    @asyncio.coroutine
    def async_update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.debug("zone type definition %s", ZoneType(self._zone.definition).name)
        self._hidden = self._zone.definition == ZoneType.Disabled.value
        self._state = ZoneLogicalStatus(self._zone.logical_status).name
