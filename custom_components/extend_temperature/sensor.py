"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import random
import logging
import time
import homeassistant
from typing import Optional
from homeassistant.const import (
    CONF_TEMPERATURE_UNIT,
    DEVICE_CLASS_BATTERY,
    PERCENTAGE,
    DEVICE_CLASS_ILLUMINANCE,
    ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT, CONF_ICON_TEMPLATE,
    CONF_ENTITY_PICTURE_TEMPLATE, CONF_SENSORS, EVENT_HOMEASSISTANT_START,
    MATCH_ALL, CONF_DEVICE_CLASS, DEVICE_CLASS_TEMPERATURE, STATE_UNKNOWN,
    STATE_UNAVAILABLE, DEVICE_CLASS_HUMIDITY, ATTR_TEMPERATURE, TEMP_FAHRENHEIT,
    CONF_UNIQUE_ID,
)

from homeassistant.components.mold_indicator.sensor import MAGNUS_K2, MAGNUS_K3
from homeassistant.components.sensor import ENTITY_ID_FORMAT, \
    PLATFORM_SCHEMA, DEVICE_CLASSES_SCHEMA

from homeassistant.const import ATTR_VOLTAGE
import asyncio

from homeassistant import components
from homeassistant import util
from homeassistant.helpers.entity import Entity

from custom_components.extend_temperature.mold import ATTR_CRITICAL_TEMP, ATTR_DEWPOINT
from .const import *
from homeassistant.exceptions import TemplateError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change

import locale
import math

_LOGGER = logging.getLogger(__name__)

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.
async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""
    
    _LOGGER.error("call async setup entry")
    currentLocale = "en"
    if(locale.getlocale()[0] == 'Korean_Korea'):
        currentLocale = "ko"
    else:
        currentLocale = "en"

    device = Device(config_entry.data.get("device_name"))

    _LOGGER.error("config_entry data : %s", config_entry.data)
    _LOGGER.error("config_entry options : %s", config_entry.options)

    indoor_temp_entity = config_entry.data.get(CONF_INDOOR_TEMP_ENTITY)
    humidi_entity = config_entry.data.get(CONF_HUMIDITY_ENTITY)
    wind_entity = config_entry.options.get(CONF_WIND_ENTITY)
    outdoor_temp_entity = config_entry.options.get(CONF_OUTDOOR_TEMP_ENTITY)
    mold_calib_factor = config_entry.options.get(CONF_MOLD_CALIB_FACTOR)
    
    new_devices = []

    for sensor_type in SENSOR_TYPES:       
        if outdoor_temp_entity == None or outdoor_temp_entity == '' or outdoor_temp_entity == ' ':
            #if wind_entity == None or wind_entity == '' or wind_entity == ' ':
            #    if sensor_type == STYPE_WIND_SPEED:
            #        continue
            if sensor_type == STYPE_OUTDOOR_TEMP or sensor_type == STYPE_MOLD_INDICATOR or sensor_type == STYPE_APPARENT_TEMP:
                continue
        if wind_entity == None or wind_entity == '' or wind_entity == ' ':
            if sensor_type == STYPE_WIND_SPEED or sensor_type == STYPE_APPARENT_TEMP:
                    continue
        new_devices.append(
                ExtendSensor(
                        hass,
                        device,
                        sensor_type,
                        indoor_temp_entity,
                        humidi_entity,
                        outdoor_temp_entity,
                        wind_entity,
                        mold_calib_factor,
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

    def __init__(self, hass, device, sensor_type, indoor_temp_entity, humidi_entity, outdoor_temp_entity, wind_entity, mold_calib_factor, unique_id, currentLocale):
        """Initialize the sensor."""
        super().__init__(device)

        self.hass = hass
        self.entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, "{}_{}".format(device.device_id, sensor_type), hass=hass)
        self._name = "{} {}".format(device.device_id, TRANSLATION[currentLocale][sensor_type])
        #self._name = "{} {}".format(device.device_id, SENSOR_TYPES[sensor_type][1])
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._state = None
        self._device_state_attributes = {}
        self._icon = None
        self._entity_picture = None
        self._indoor_temp_entity = indoor_temp_entity
        self._humidi_entity = humidi_entity
        self._outdoor_temp_entity = outdoor_temp_entity
        self._wind_entity = wind_entity
        self._mold_calib_factor = mold_calib_factor
        self._device_class = SENSOR_TYPES[sensor_type][0]
        self._sensor_type = sensor_type
        self._indoor_temp = None
        self._outdoor_temp = None
        self._humidity = None
        self._unique_id = unique_id
        self._device = device
        self._wind = None

        async_track_state_change(
            self.hass, self._indoor_temp_entity, self.indoor_temp_state_listener)

        async_track_state_change(
            self.hass, self._humidi_entity, self.humidity_state_listener)
        
        if self._wind_entity != None:
            async_track_state_change(
                self.hass, self._wind_entity, self.wind_state_listener)
            wind_state = hass.states.get(self._wind_entity)
            if _is_valid_state(wind_state):
                self._wind = float(wind_state.state)

        if self._outdoor_temp_entity != None:
            async_track_state_change(
                self.hass, self._outdoor_temp_entity, self.outdoor_temp_state_listener)
            outdoor_temp_state = hass.states.get(self._outdoor_temp_entity)
            if _is_valid_state(outdoor_temp_state):
                self._outdoor_temp = float(outdoor_temp_state.state)

        indoor_temp_state = hass.states.get(self._indoor_temp_entity)
        if _is_valid_state(indoor_temp_state):
            self._indoor_temp = float(indoor_temp_state.state)

        humidity_state = hass.states.get(self._humidi_entity)
        if _is_valid_state(humidity_state):
            self._humidity = float(humidity_state.state)


    def indoor_temp_state_listener(self, entity, old_state, new_state):
        """Handle temperature device state changes."""
        if _is_valid_state(new_state):
            unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
            temp = util.convert(new_state.state, float)
            # convert to celsius if necessary
            if unit == TEMP_FAHRENHEIT:
                temp = util.temperature.fahrenheit_to_celsius(temp)
            self._indoor_temp = temp

        self.async_schedule_update_ha_state(True)

    def outdoor_temp_state_listener(self, entity, old_state, new_state):
        """Handle temperature device state changes."""
        if _is_valid_state(new_state):
            unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
            temp = util.convert(new_state.state, float)
            # convert to celsius if necessary
            if unit == TEMP_FAHRENHEIT:
                temp = util.temperature.fahrenheit_to_celsius(temp)
            self._outdoor_temp = temp

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
        """Calculate the dewpoint for the indoor air."""
        # Use magnus approximation to calculate the dew point
        alpha = MAGNUS_K2 * temperature / (MAGNUS_K3 + temperature)
        beta = MAGNUS_K2 * MAGNUS_K3 / (MAGNUS_K3 + temperature)
        dewpoint = 0
        if humidity == 0:
            dewpoint = -50  # not defined, assume very low value
        else:
            dewpoint = (
                MAGNUS_K3
                * (alpha + math.log(humidity / 100.0))
                / (beta - math.log(humidity / 100.0))
            )
        return round(dewpoint, 2)

    def computeCriticalTemp(self, indoor_temp, outdoor_temp, calib_factor):
        _crit_temp = (
            outdoor_temp
            + (indoor_temp - outdoor_temp) / calib_factor
        )
        return _crit_temp

    def computeMoldIndicator(self, indoor_temp, outdoor_temp, humidity, calib_factor):
        """Calculate the humidity at the (cold) calibration point."""
        dewpoint = self.computeDewPoint(indoor_temp, humidity)
        crit_temp = self.computeCriticalTemp(indoor_temp, outdoor_temp, calib_factor)
        mold = None
        # Then calculate the humidity at this point
        alpha = MAGNUS_K2 * crit_temp / (MAGNUS_K3 + crit_temp)
        beta = MAGNUS_K2 * MAGNUS_K3 / (MAGNUS_K3 + crit_temp)

        crit_humidity = (
            math.exp(
                (dewpoint * beta - MAGNUS_K3 * alpha)
                / (dewpoint + MAGNUS_K3)
            )
            * 100.0
        )

        # check bounds and format
        if crit_humidity > 100:
            mold = "100"
        elif crit_humidity < 0:
            mold = "0"
        else:
            mold = f"{int(crit_humidity):d}"

        return mold

        """http://wahiduddin.net/calc/density_algorithms.htm"""
        #A0 = 373.15 / (273.15 + temperature)
        #SUM = -7.90298 * (A0 - 1)
        #SUM += 5.02808 * math.log(A0, 10)
        #SUM += -1.3816e-7 * (pow(10, (11.344 * (1 - 1 / A0))) - 1)
        #SUM += 8.1328e-3 * (pow(10, (-3.49149 * (A0 - 1))) - 1)
        #SUM += math.log(1013.246, 10)
        #VP = pow(10, SUM - 3) * humidity
        #Td = math.log(VP / 0.61078)
        #Td = (241.88 * Td) / (17.558 - Td)
        #return round(Td, 2)

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
            return self._unique_id

    def update(self):
        """Update the state."""
        value = None

        if not math.isnan(self._indoor_temp) and not math.isnan(self._humidity):
            if self._sensor_type == STYPE_DEWPOINT:
                value = self.computeDewPoint(self._indoor_temp, self._humidity)
            if self._sensor_type == STYPE_HEATINDEX:
                value = self.computeHeatIndex(self._indoor_temp, self._humidity)
            elif self._sensor_type == STYPE_HUMIDI_STATE:
                value = self.computeHumidiState(self._indoor_temp, self._humidity)
            elif self._sensor_type == STYPE_A_HUMIDI:
                value = self.computeAbsoluteHumidity(self._indoor_temp, self._humidity)
            elif self._sensor_type == STYPE_HEATINDEX_STATE:
                value = self.computeHeatIndexState(self._indoor_temp, self._humidity)
            elif self._sensor_type == STYPE_R_HUMIDI:
                value = self._humidity
            elif self._sensor_type == STYPE_INDOOR_TEMP:
                value = self._indoor_temp
            elif self._sensor_type == STYPE_APPARENT_TEMP and not math.isnan(self._wind) and not math.isnan(self._outdoor_temp):
                value = self.computeApparentTemperature(self._outdoor_temp, self._wind)
                #self._device_state_attributes[ATTR_WIND] = self._wind
            elif self._sensor_type == STYPE_WIND_SPEED and not math.isnan(self._wind):
                value = self._wind
            elif self._sensor_type == STYPE_MOLD_INDICATOR and not math.isnan(self._outdoor_temp):
                value = self.computeMoldIndicator(self._indoor_temp, self._outdoor_temp, self._humidity, self._mold_calib_factor)
                self._device_state_attributes[ATTR_DEWPOINT] = self.computeDewPoint(self._indoor_temp, self._humidity)
                self._device_state_attributes[ATTR_CRITICAL_TEMP] = self.computeCriticalTemp(self._indoor_temp, self._outdoor_temp, self._mold_calib_factor)
            elif self._sensor_type == STYPE_OUTDOOR_TEMP and not math.isnan(self._outdoor_temp):
                value = self._outdoor_temp
            
            self._state = value
            self._device_state_attributes[ATTR_INDOOR_TEMPERATURE] = self._indoor_temp
            self._device_state_attributes[ATTR_HUMIDITY] = self._humidity
            if self._outdoor_temp != None:
                self._device_state_attributes[ATTR_OUTDOOR_TEMPERATURE] = self._outdoor_temp
            if self._wind != None:
                self._device_state_attributes[ATTR_WIND] = self._wind

    async def async_update(self):
        """Update the state."""
        self.update()

def _is_valid_state(state) -> bool:
    return state and state.state != STATE_UNKNOWN and state.state != STATE_UNAVAILABLE and not math.isnan(float(state.state))
