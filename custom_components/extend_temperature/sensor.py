"""Platform for sensor integration."""
import logging
import datetime
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT, STATE_UNKNOWN,
    STATE_UNAVAILABLE, UnitOfTemperature
)

from operator import eq
from homeassistant.core import Event, EventStateChangedData, callback
from homeassistant.components.sensor import ENTITY_ID_FORMAT
import asyncio

from homeassistant import util
from homeassistant.components.sensor import SensorEntity

from homeassistant.components.mold_indicator.sensor import ATTR_CRITICAL_TEMP, ATTR_DEWPOINT
from .const import *
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change_event

import math

MAGNUS_K2 = 17.62
MAGNUS_K3 = 243.12

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""

    hass.data[DOMAIN]["listener"] = []

    device = Device(config_entry.data.get(CONF_DEVICE_NAME))

    inside_temp_entity = config_entry.data.get(CONF_INSIDE_TEMP_ENTITY)

    if config_entry.options != None:
        if config_entry.options.get(CONF_INSIDE_TEMP_ENTITY) != None:
            inside_temp_entity = config_entry.options.get(
                CONF_INSIDE_TEMP_ENTITY)

    humidi_entity = config_entry.data.get(CONF_HUMIDITY_ENTITY)

    if config_entry.options != None:
        if config_entry.options.get(CONF_HUMIDITY_ENTITY) != None:
            humidi_entity = config_entry.options.get(CONF_HUMIDITY_ENTITY)

    wind_entity = config_entry.options.get(CONF_WIND_ENTITY)
    outside_temp_entity = config_entry.options.get(CONF_OUTSIDE_TEMP_ENTITY)
    mold_calib_factor = config_entry.options.get(CONF_MOLD_CALIB_FACTOR)
    apparent_temp_source_entity = config_entry.options.get(
        CONF_APPARENT_TEMP_SOURCE_ENTITY)
    apparent_hum_source_entity = config_entry.options.get(
        CONF_APPARENT_HUM_SOURCE_ENTITY)
    decimal_places = config_entry.options.get(CONF_DECIMAL_PLACES)

    if None == decimal_places:
        decimal_places = 2

    if None == mold_calib_factor:
        mold_calib_factor = 2.0
    else:
        mold_calib_factor = (float)(mold_calib_factor)
    new_devices = []

    for sensor_type in SENSOR_TYPES:
        if apparent_temp_source_entity == None or apparent_temp_source_entity == '' or apparent_temp_source_entity == ' ':
            if sensor_type == STYPE_APPARENT_TEMP:
                continue

        if apparent_hum_source_entity == None or apparent_hum_source_entity == '' or apparent_hum_source_entity == ' ':
            if sensor_type == STYPE_APPARENT_HUM:
                continue

        if wind_entity == None or wind_entity == '' or wind_entity == ' ':
            if sensor_type == STYPE_WIND_SPEED or sensor_type == STYPE_APPARENT_TEMP:
                continue

        if outside_temp_entity == None or outside_temp_entity == '' or outside_temp_entity == ' ':
            if sensor_type == STYPE_OUTSIDE_TEMP or sensor_type == STYPE_MOLD_INDICATOR:
                continue

        new_devices.append(
            ExtendSensor(
                hass,
                config_entry,
                device,
                sensor_type,
                inside_temp_entity,
                humidi_entity,
                outside_temp_entity,
                wind_entity,
                apparent_temp_source_entity,
                apparent_hum_source_entity,
                mold_calib_factor,
                decimal_places,
                device.device_id + sensor_type,
            )
        )

    if new_devices:
        async_add_devices(new_devices)



class SensorBase(SensorEntity):
    """Base representation of a Hello World Sensor."""

    should_poll = False

    def __init__(self, device):
        """Initialize the sensor."""
        self._device = device

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
        # return self._roller.online and self._roller.hub.online

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
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass, config, device, sensor_type, inside_temp_entity, humidi_entity, outside_temp_entity, wind_entity,
                 apparent_temp_source_entity, apparent_hum_source_entity, mold_calib_factor, decimal_places, unique_id):
        """Initialize the sensor."""
        super().__init__(device)

        self.hass = hass
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(device.device_id, sensor_type), hass=hass)
        _LOGGER.debug("entity id : " + str(self.entity_id))
        # self._name = "{} {}".format(
        #     device.device_id, TRANSLATION[currentLocale][sensor_type])
        # self._name = "{} {}".format(device.device_id, SENSOR_TYPES[sensor_type][1])
        self._attr_unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._attr_extra_state_attributes = {}
        self._state = None
        self._inside_temp_entity = inside_temp_entity
        self._humidi_entity = humidi_entity
        self._outside_temp_entity = outside_temp_entity
        self._apparent_temp_source_entity = apparent_temp_source_entity
        self._apparent_hum_source_entity = apparent_hum_source_entity
        self._wind_entity = wind_entity
        self._mold_calib_factor = mold_calib_factor
        self._decimal_places = decimal_places
        self._attr_device_class = SENSOR_TYPES[sensor_type][0]
        self._attr_icon = SENSOR_TYPES[sensor_type][2]
        self._sensor_type = sensor_type
        self._inside_temp = None
        self._outside_temp = None
        self._humidity = None
        self._attr_unique_id = unique_id
        self._device = device
        self._wind = None
        self._apparent_temp_source = None
        self._apparent_hum_source = None
        self._decimal_calc_type = config.options.get(CONF_DECIMAL_CALC_TYPE)

        if self._wind_entity != None:
            self._wind = self.setStateListener(
                hass, self._wind_entity, self.wind_state_listener)

        if self._apparent_temp_source_entity != None:
            self._apparent_temp_source = self.setStateListener(
                hass, self._apparent_temp_source_entity, self.apparent_temp_source_state_listener)

        if self._apparent_hum_source_entity != None:
            self._apparent_hum_source = self.setStateListener(
                hass, self._apparent_hum_source_entity, self.apparent_hum_source_state_listener)

        if self._outside_temp_entity != None:
            self._outside_temp = self.setStateListener(
                hass, self._outside_temp_entity, self.outside_temp_state_listener)

        self._inside_temp = self.setStateListener(
            hass, self._inside_temp_entity, self.inside_temp_state_listener)
        self._humidity = self.setStateListener(
            hass, self._humidi_entity, self.humidity_state_listener)

        self.update()

    def setStateListener(self, hass, entity, listener):
        hass.data[DOMAIN]["listener"].append(async_track_state_change_event(
            self.hass, entity, listener))

        entity_state = self.hass.states.get(entity)
        if _is_valid_state(entity_state):
            return float(entity_state.state)

    @callback
    async def apparent_temp_source_state_listener(self, event: Event):
        entity = event.data["entity_id"]
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        try:
            """Handle temperature device state changes."""
            if _is_valid_state(new_state):
                unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
                temp = util.convert(new_state.state, float)
                # convert to celsius if necessary
                if unit == UnitOfTemperature.FAHRENHEIT:
                    temp = util.temperature.fahrenheit_to_celsius(temp)
                self._apparent_temp_source = temp
            else:
                self._apparent_temp_source = STATE_UNKNOWN
            await self.async_schedule_update_ha_state(True)
        except:
            ''

    @callback
    async def apparent_hum_source_state_listener(self, event: Event):
        entity = event.data["entity_id"]
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        try:
            """Handle temperature device state changes."""
            if _is_valid_state(new_state):
                self._apparent_hum_source = float(new_state.state)
            else:
                self._apparent_hum_source = STATE_UNKNOWN
            await self.async_schedule_update_ha_state(True)
        except:
            ''

    @callback
    async def inside_temp_state_listener(self, event: Event):
        entity = event.data["entity_id"]
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        try:
            """Handle temperature device state changes."""
            if _is_valid_state(new_state):
                unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
                temp = util.convert(new_state.state, float)
                # convert to celsius if necessary
                if unit == UnitOfTemperature.FAHRENHEIT:
                    temp = util.temperature.fahrenheit_to_celsius(temp)
                self._inside_temp = temp
            else:
                self._inside_temp = STATE_UNKNOWN
            await self.async_schedule_update_ha_state(True)
        except:
            ''

    @callback
    async def outside_temp_state_listener(self, event:Event):
        entity = event.data["entity_id"]
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        try:
            """Handle temperature device state changes."""
            if _is_valid_state(new_state):
                unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
                temp = util.convert(new_state.state, float)
                # convert to celsius if necessary
                if unit == UnitOfTemperature.FAHRENHEIT:
                    temp = util.temperature.fahrenheit_to_celsius(temp)
                self._outside_temp = temp
            else:
                self._outside_temp = STATE_UNKNOWN
            await self.async_schedule_update_ha_state(True)
        except:
            ''

    @callback
    async def humidity_state_listener(self, event:Event):
        entity = event.data["entity_id"]
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        try:
            """Handle humidity device state changes."""
            if _is_valid_state(new_state):
                self._humidity = float(new_state.state)
            else:
                self._humidity = STATE_UNKNOWN
            await self.async_schedule_update_ha_state(True)
        except:
            ''

    @callback
    async def wind_state_listener(self, event:Event):
        entity = event.data["entity_id"]
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        try:
            """Handle humidity device state changes."""
            if _is_valid_state(new_state):
                self._wind = float(new_state.state)
            else:
                self._wind = STATE_UNKNOWN
            await self.async_schedule_update_ha_state(True)
        except:
            ''

    def computeDewPoint(self, temperature, humidity):
        """Calculate the dewpoint for the inside air."""
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
        return self.decimal_correction(dewpoint)

    def computeCriticalTemp(self, inside_temp, outside_temp, calib_factor):
        _crit_temp = (
            outside_temp
            + (inside_temp - outside_temp) / calib_factor
        )
        return self.decimal_correction(_crit_temp)

    def computeMoldIndicator(self, inside_temp, outside_temp, humidity, calib_factor):
        """Calculate Mold Indicator"""
        dewpoint = self.computeDewPoint(inside_temp, humidity)
        crit_temp = self.computeCriticalTemp(
            inside_temp, outside_temp, calib_factor)
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
        # A0 = 373.15 / (273.15 + temperature)
        # SUM = -7.90298 * (A0 - 1)
        # SUM += 5.02808 * math.log(A0, 10)
        # SUM += -1.3816e-7 * (pow(10, (11.344 * (1 - 1 / A0))) - 1)
        # SUM += 8.1328e-3 * (pow(10, (-3.49149 * (A0 - 1))) - 1)
        # SUM += math.log(1013.246, 10)
        # VP = pow(10, SUM - 3) * humidity
        # Td = math.log(VP / 0.61078)
        # Td = (241.88 * Td) / (17.558 - Td)
        # return round(Td, 2)

    def toFahrenheit(self, celsius):
        """celsius to fahrenheit"""
        return 1.8 * celsius + 32.0

    def toCelsius(self, fahrenheit):
        """fahrenheit to celsius"""
        return (fahrenheit - 32.0) / 1.8

    def computeHeatIndex(self, temperature, humidity):
        """http://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml"""
        fahrenheit = self.toFahrenheit(temperature)
        hi = 0.5 * (fahrenheit + 61.0 +
                    ((fahrenheit - 68.0) * 1.2) + (humidity * 0.094))

        if hi > 79:
            hi = -42.379 + 2.04901523 * fahrenheit
            hi = hi + 10.14333127 * humidity
            hi = hi + -0.22475541 * fahrenheit * humidity
            hi = hi + -0.00683783 * pow(fahrenheit, 2)
            hi = hi + -0.05481717 * pow(humidity, 2)
            hi = hi + 0.00122874 * pow(fahrenheit, 2) * humidity
            hi = hi + 0.00085282 * fahrenheit * pow(humidity, 2)
            hi = hi + -0.00000199 * pow(fahrenheit, 2) * pow(humidity, 2)

        if humidity < 13 and fahrenheit >= 80 and fahrenheit <= 112:
            hi = hi - ((13 - humidity) * 0.25) * \
                math.sqrt((17 - abs(fahrenheit - 95)) * 0.05882)
        elif humidity > 85 and fahrenheit >= 80 and fahrenheit <= 87:
            hi = hi + ((humidity - 85) * 0.1) * ((87 - fahrenheit) * 0.2)

        return self.decimal_correction(self.toCelsius(hi))

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
        absTemperature = temperature + 273.15
        absHumidity = 6.112
        absHumidity *= math.exp((17.67 * temperature) / (243.5 + temperature))
        absHumidity *= humidity
        absHumidity *= 2.1674
        absHumidity /= absTemperature
        return self.decimal_correction(absHumidity)

    def computeApparentTemperature(self, temperature, humidity, wind):
        T = temperature
        H = humidity
        W = wind * 3.6
        if datetime.datetime.today().month >= 5 and datetime.datetime.today().month <= 9:
            """ 하계용 체감온도 계산 """
            TW = T*math.atan(0.151977*(math.pow(H+8.313659, 1/2)))+math.atan(T+H)-math.atan(
                H-1.67633)+0.00391838*math.pow(H, 3/2)*math.atan(0.023101*H)-4.686035
            apparent_temperature = -0.2442+0.55399*TW+0.45535*T - \
                0.0022*math.pow(TW, 2)+0.00278*TW*T+3.0
        else:
            if W > 4.8:
                W = math.pow(W, 0.16)
                apparent_temperature = 13.12 + 0.6215 * T - 11.37 * W + 0.3965 * W * T
                if (apparent_temperature > T):
                    apparent_temperature = T
            else:
                apparent_temperature = T

        return self.decimal_correction(apparent_temperature)

    """Sensor Properties"""
    @property
    def translation_key(self) -> str | None:
        return self._sensor_type

    # @property
    # def name(self):
    #     """Return the name of the sensor."""
    #     return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return self._attr_unit_of_measurement

    @property
    def suggested_display_precision(self) -> int | None:
        return self._decimal_places if self._sensor_type in (STYPE_HUMIDI_STATE, STYPE_HEATINDEX_STATE) else None
        
    def update(self):
        """Update the state."""
        # while True:
        # _LOGGER.error("check valid")
        # time.sleep(1)
        # if _is_valid_state(self.hass.states.get(self._inside_temp_entity)) and _is_valid_state(self.hass.states.get(self._humidi_entity)):
        #    _LOGGER.error("check valid end")
        #    break
        value = STATE_UNKNOWN

        if isNumber(self._inside_temp) and isNumber(self._humidity):
            if self._sensor_type == STYPE_DEWPOINT:
                value = self.computeDewPoint(self._inside_temp, self._humidity)
            if self._sensor_type == STYPE_HEATINDEX:
                value = self.computeHeatIndex(
                    self._inside_temp, self._humidity)
            elif self._sensor_type == STYPE_HUMIDI_STATE:
                value = self.computeHumidiState(self._inside_temp, self._humidity)
            elif self._sensor_type == STYPE_A_HUMIDI:
                value = self.computeAbsoluteHumidity(
                    self._inside_temp, self._humidity)
            elif self._sensor_type == STYPE_HEATINDEX_STATE:
                value = self.computeHeatIndexState(self._inside_temp, self._humidity)
            elif self._sensor_type == STYPE_R_HUMIDI:
                value = self._humidity
            elif self._sensor_type == STYPE_INSIDE_TEMP:
                value = self._inside_temp
            elif self._sensor_type == STYPE_APPARENT_TEMP and isNumber(self._wind) and isNumber(self._apparent_temp_source) and isNumber(self._apparent_hum_source):
                value = self.computeApparentTemperature(
                    self._apparent_temp_source, self._apparent_hum_source, self._wind)
            elif self._sensor_type == STYPE_WIND_SPEED and isNumber(self._wind):
                value = self._wind
            elif self._sensor_type == STYPE_MOLD_INDICATOR and isNumber(self._outside_temp):
                value = self.computeMoldIndicator(
                    self._inside_temp, self._outside_temp, self._humidity, self._mold_calib_factor)
                self._attr_extra_state_attributes[ATTR_DEWPOINT] = self.computeDewPoint(
                    self._inside_temp, self._humidity)
                self._attr_extra_state_attributes[ATTR_CRITICAL_TEMP] = self.computeCriticalTemp(
                    self._inside_temp, self._outside_temp, self._mold_calib_factor)
            elif self._sensor_type == STYPE_OUTSIDE_TEMP and isNumber(self._outside_temp):
                value = self._outside_temp

            if isNumber(value):
                value = self.decimal_correction(float(value))

            self._attr_extra_state_attributes[ATTR_INSIDE_TEMPERATURE] = self._inside_temp
            self._attr_extra_state_attributes[ATTR_HUMIDITY] = self._humidity
            if self._outside_temp != None:
                self._attr_extra_state_attributes[ATTR_OUTSIDE_TEMPERATURE] = self._outside_temp
            if self._wind != None:
                self._attr_extra_state_attributes[ATTR_WIND] = self._wind

        self._state = value

    async def async_update(self):
        """Update the state."""
        self.update()

    def decimal_correction(self, value):
        if eq(self._decimal_calc_type, ROUND):
            return round(value, self._decimal_places)
        elif eq(self._decimal_calc_type, CEIL):
            return math.ceil(value * 10 ** self._decimal_places) / 10 ** self._decimal_places
        else:
            return math.trunc(value * 10 ** self._decimal_places) / 10 ** self._decimal_places


def _is_real_number(value) -> bool:
    try:
        return value != None and not math.isnan(value)
    except:
        return False


def isNumber(s):
    try:
        if s != None:
            float(s)
            return True
        else:
            return False
    except ValueError:
        return False


def _is_valid_state(state) -> bool:
    try:
        return state and state.state != STATE_UNKNOWN and state.state != STATE_UNAVAILABLE and not math.isnan(float(state.state))
    except:
        return False
