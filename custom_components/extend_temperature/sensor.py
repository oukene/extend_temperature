"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import random
import logging

from typing import Optional
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    PERCENTAGE,
    DEVICE_CLASS_ILLUMINANCE,
    ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT, CONF_ICON_TEMPLATE,
    CONF_ENTITY_PICTURE_TEMPLATE, CONF_SENSORS, EVENT_HOMEASSISTANT_START,
    MATCH_ALL, CONF_DEVICE_CLASS, DEVICE_CLASS_TEMPERATURE, STATE_UNKNOWN,
    STATE_UNAVAILABLE, DEVICE_CLASS_HUMIDITY, ATTR_TEMPERATURE, TEMP_FAHRENHEIT,
    CONF_UNIQUE_ID,
)
from homeassistant.components.sensor import ENTITY_ID_FORMAT, \
    PLATFORM_SCHEMA, DEVICE_CLASSES_SCHEMA

from homeassistant.const import ATTR_VOLTAGE
import asyncio

from homeassistant import components
from homeassistant import util
from homeassistant.helpers.entity import Entity
from .const import DOMAIN, VERSION, TRANSLATION
from homeassistant.exceptions import TemplateError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change

import locale
import math

_LOGGER = logging.getLogger(__name__)

CONF_TEMPERATURE_SENSOR = 'temperature_entity'
CONF_HUMIDITY_SENSOR = 'humidity_entity'
CONF_WIND_SENSOR = 'wind_entity'
ATTR_HUMIDITY = 'humidity'
ATTR_WIND = 'wind'


SENSOR_TYPES = {
    'temperature': [DEVICE_CLASS_TEMPERATURE, 'Temperature', '°C'],
    'relativehumidity': [DEVICE_CLASS_HUMIDITY, 'Relative Humidity', '%'],
    'absolutehumidity': [DEVICE_CLASS_HUMIDITY, 'Absolute Humidity', 'g/m³'],
    'heatindex': [DEVICE_CLASS_TEMPERATURE, 'Heat Index', '°C'],
    'apparent_temperature': [DEVICE_CLASS_TEMPERATURE, 'Apparent Temperature', '°C'],
    'dewpoint': [DEVICE_CLASS_TEMPERATURE, 'Dew Point', '°C'],
    'humidi_state': [DOMAIN + "__humidi_state", 'Humidity State', None],
    'heatindex_state': [DOMAIN + "__heatindex_state", 'Heat Index State', None],
    'wind_speed': [None, 'Wind Speed', 'm/s'],
}

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.
async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""
    
    currentLocale = 1
    if(locale.getlocale()[0] == 'Korean_Korea'):
        currentLocale = "ko"
    else:
        currentLocale = "en"

    device = Device(config_entry.data.get("device_name"))

    temperature_entity = config_entry.data.get(CONF_TEMPERATURE_SENSOR)
    humidity_entity = config_entry.data.get(CONF_HUMIDITY_SENSOR)
    wind_entity = config_entry.data.get(CONF_WIND_SENSOR)
    new_devices = []

    for sensor_type in SENSOR_TYPES:
        if wind_entity == None:
            if sensor_type == "apparent_temperature":
                continue
        new_devices.append(
                ExtendSensor(
                        hass,
                        device,
                        temperature_entity,
                        humidity_entity,
                        wind_entity,
                        sensor_type,
                        device.device_id + sensor_type,
                        currentLocale
                )
        )

    if new_devices:
        async_add_devices(new_devices)


# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.
class SensorBase(Entity):
    """Base representation of a Hello World Sensor."""

    should_poll = False
    
    def __init__(self, device):
        """Initialize the sensor."""
        self._device = device

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._device.device_id)},
            # If desired, the name for the device could be different to the entity
            "name": self._device.device_id,
            "sw_version": self._device.firmware_version,
            "model": self._device.model,
            "manufacturer": self._device.manufacturer
        }

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True
        #return self._roller.online and self._roller.hub.online
        
    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)


class Device:
    """Dummy roller (device for HA) for Hello World example."""

    def __init__(self, name):
        """Init dummy roller."""
        self._id = name
        self.name = name
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        # Reports if the roller is moving up or down.
        # >0 is up, <0 is down. This very much just for demonstration.

        # Some static information about this device
        # Some static information about this device
        self.firmware_version = VERSION
        self.model = "Extend Temperature"
        self.manufacturer = "Extend Temperature"

    @property
    def device_id(self):
        """Return ID for roller."""
        return self._id

    def register_callback(self, callback):
        """Register callback, called when Roller changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def publish_updates(self):
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

class ExtendSensor(SensorBase):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, device, temperature_entity, humidity_entity, wind_entity, sensor_type, unique_id, currentLocale):
        """Initialize the sensor."""
        super().__init__(device)

        self.hass = hass
        self.entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, "{}_{}".format(device.device_id, sensor_type), hass=hass)
        self._name = "{} {}".format(device.device_id, TRANSLATION[currentLocale][sensor_type])
        #self._name = "{} {}".format(device.device_id, SENSOR_TYPES[sensor_type][1])
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][2]
        self._state = None
        self._device_state_attributes = {}
        self._icon = None
        self._entity_picture = None
        self._temperature_entity = temperature_entity
        self._humidity_entity = humidity_entity
        self._wind_entity = wind_entity
        self._device_class = SENSOR_TYPES[sensor_type][0]
        self._sensor_type = sensor_type
        self._temperature = None
        self._humidity = None
        self._unique_id = unique_id
        self._device = device
        self._wind = None

        async_track_state_change(
            self.hass, self._temperature_entity, self.temperature_state_listener)

        async_track_state_change(
            self.hass, self._humidity_entity, self.humidity_state_listener)
        
        if wind_entity != None:
            async_track_state_change(
                self.hass, self._wind_entity, self.wind_state_listener)

        temperature_state = hass.states.get(temperature_entity)
        if _is_valid_state(temperature_state):
            self._temperature = float(temperature_state.state)

        humidity_state = hass.states.get(humidity_entity)
        if _is_valid_state(humidity_state):
            self._humidity = float(humidity_state.state)

        if wind_entity != None:
            wind_state = hass.states.get(wind_entity)
            if _is_valid_state(wind_state):
                self._wind = float(wind_state.state)
        
        #self.update()

    def temperature_state_listener(self, entity, old_state, new_state):
        """Handle temperature device state changes."""
        if _is_valid_state(new_state):
            unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
            temp = util.convert(new_state.state, float)
            # convert to celsius if necessary
            if unit == TEMP_FAHRENHEIT:
                temp = util.temperature.fahrenheit_to_celsius(temp)
            self._temperature = temp

        self.async_schedule_update_ha_state(True)

    def humidity_state_listener(self, entity, old_state, new_state):
        """Handle humidity device state changes."""
        if _is_valid_state(new_state):
            self._humidity = float(new_state.state)

        self.async_schedule_update_ha_state(True)

    def wind_state_listener(self, entity, old_state, new_state):
        """Handle humidity device state changes."""
        if _is_valid_state(new_state):
            self._wind = float(new_state.state)

        self.async_schedule_update_ha_state(True)

    def computeDewPoint(self, temperature, humidity):
        """http://wahiduddin.net/calc/density_algorithms.htm"""
        A0 = 373.15 / (273.15 + temperature)
        SUM = -7.90298 * (A0 - 1)
        SUM += 5.02808 * math.log(A0, 10)
        SUM += -1.3816e-7 * (pow(10, (11.344 * (1 - 1 / A0))) - 1)
        SUM += 8.1328e-3 * (pow(10, (-3.49149 * (A0 - 1))) - 1)
        SUM += math.log(1013.246, 10)
        VP = pow(10, SUM - 3) * humidity
        Td = math.log(VP / 0.61078)
        Td = (241.88 * Td) / (17.558 - Td)
        return round(Td, 2)

    def toFahrenheit(self, celsius):
        """celsius to fahrenheit"""
        return 1.8 * celsius + 32.0

    def toCelsius(self, fahrenheit):
        """fahrenheit to celsius"""
        return (fahrenheit - 32.0) / 1.8

    def computeHeatIndex(self, temperature, humidity):
        """http://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml"""
        fahrenheit = self.toFahrenheit(temperature)
        hi = 0.5 * (fahrenheit + 61.0 + ((fahrenheit - 68.0) * 1.2) + (humidity * 0.094));

        if hi > 79:
            hi = -42.379 + 2.04901523 * fahrenheit
            hi = hi + 10.14333127 * humidity
            hi = hi + -0.22475541 * fahrenheit * humidity
            hi = hi + -0.00683783 * pow(fahrenheit, 2)
            hi = hi + -0.05481717 * pow(humidity, 2)
            hi = hi + 0.00122874 * pow(fahrenheit, 2) * humidity
            hi = hi + 0.00085282 * fahrenheit * pow(humidity, 2)
            hi = hi + -0.00000199 * pow(fahrenheit, 2) * pow(humidity, 2);

        if humidity < 13 and fahrenheit >= 80 and fahrenheit <= 112:
            hi = hi - ((13 - humidity) * 0.25) * math.sqrt((17 - abs(fahrenheit - 95)) * 0.05882)
        elif humidity > 85 and fahrenheit >= 80 and fahrenheit <= 87:
            hi = hi + ((humidity - 85) * 0.1) * ((87 - fahrenheit) * 0.2)

        return round(self.toCelsius(hi), 2)

    def unique_id(self):
        """Return Unique ID string."""
        return self.unique_id

    def computeHumidiState(self, temperature, humidity):
        """https://en.wikipedia.org/wiki/Dew_point"""
        dewPoint = self.computeDewPoint(temperature, humidity)
        if dewPoint < 10:
            return "little_dry"
        elif dewPoint < 13:
            return "very_good"
        elif dewPoint < 16:
            return "good"
        elif dewPoint < 18:
            return "little_wet"
        elif dewPoint < 21:
            return "wet"
        else:
            return "very_wet"

    def computeHeatIndexState(self, temperature, humidity):
        heatIndex = self.computeHeatIndex(temperature, humidity)
        if heatIndex < 27:
            return "good"
        elif heatIndex < 33:
            return "careful"
        elif heatIndex < 40:
            return "very_careful"
        elif heatIndex < 52:
            return "danger"
        else:
            return "very_danger"

    def computeAbsoluteHumidity(self, temperature, humidity):
        """https://carnotcycle.wordpress.com/2012/08/04/how-to-convert-relative-humidity-to-absolute-humidity/"""
        absTemperature = temperature + 273.15;
        absHumidity = 6.112;
        absHumidity *= math.exp((17.67 * temperature) / (243.5 + temperature));
        absHumidity *= humidity;
        absHumidity *= 2.1674;
        absHumidity /= absTemperature;
        return round(absHumidity, 2)

    def computeApparentTemperature(self, temperature, wind):
        wind_per_hour = wind * 60 * 60 / 1000.0
        apparent_temperature = 13.12 + 0.6215 * temperature - 11.37 * wind_per_hour ** 0.16 + 0.3965 * 0 * wind_per_hour ** 0.16
        return round(apparent_temperature, 2)


    """Sensor Properties"""
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._device_state_attributes

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def device_class(self) -> Optional[str]:
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def entity_picture(self):
        """Return the entity_picture to use in the frontend, if any."""
        return self._entity_picture

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return self._unit_of_measurement

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self._unique_id is not None:
            return self._unique_id + self._sensor_type

    def update(self):
        """Update the state."""
        value = None
        if not math.isnan(self._temperature) and not math.isnan(self._humidity) and not math.isnan(self._wind):
            if self._sensor_type == "dewpoint":
                value = self.computeDewPoint(self._temperature, self._humidity)
            if self._sensor_type == "heatindex":
                value = self.computeHeatIndex(self._temperature, self._humidity)
            elif self._sensor_type == "humidi_state":
                value = self.computeHumidiState(self._temperature, self._humidity)
            elif self._sensor_type == "absolutehumidity":
                value = self.computeAbsoluteHumidity(self._temperature, self._humidity)
            elif self._sensor_type == "apparent_temperature":
                value = self.computeApparentTemperature(self._temperature, self._wind)
            elif self._sensor_type == "heatindex_state":
                value = self.computeHeatIndexState(self._temperature, self._humidity)
            elif self._sensor_type == "relativehumidity":
                value = self._humidity
            elif self._sensor_type == "temperature":
                value = self._temperature
            elif self._sensor_type == "wind_speed":
                value = self._wind

        self._state = value
        self._device_state_attributes[ATTR_TEMPERATURE] = self._temperature
        self._device_state_attributes[ATTR_HUMIDITY] = self._humidity
        self._device_state_attributes[ATTR_WIND] = self._wind

    async def async_update(self):
        """Update the state."""
        self.update()

def _is_valid_state(state) -> bool:
    return state and state.state != STATE_UNKNOWN and state.state != STATE_UNAVAILABLE and not math.isnan(float(state.state))
