"""Constants for the Detailed Hello World Push integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import SensorDeviceClass

from homeassistant.helpers.selector import selector


# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "extend_temperature"
VERSION = "1.6.4"

CONF_DEVICE_NAME = "device_name"
CONF_INSIDE_TEMP_ENTITY = 'inside_temp_entity'
CONF_HUMIDITY_ENTITY = 'humidity_entity'
CONF_OUTSIDE_TEMP_ENTITY = "outside_temp_entity"
CONF_WIND_ENTITY = 'wind_entity'
CONF_MOLD_CALIB_FACTOR = "mold_calib_factor"
CONF_APPARENT_TEMP_SOURCE_ENTITY = "apparent_temp_source_entity"
CONF_APPARENT_HUM_SOURCE_ENTITY = "apparent_hum_source_entity"
CONF_DECIMAL_PLACES = "decial_places"
CONF_DECIMAL_CALC_TYPE = "decial_calc_type"
CONF_SENSOR_LANGUAGE = 'sensor_language'

ATTR_HUMIDITY = 'humidity'
ATTR_WIND = 'wind'
ATTR_INSIDE_TEMPERATURE = "inside temperature"
ATTR_OUTSIDE_TEMPERATURE = "outside temperature"

STYPE_INSIDE_TEMP = "inside_temperature"
STYPE_R_HUMIDI = "relative_humidity"
STYPE_A_HUMIDI = "absolute_humidity"
STYPE_HEATINDEX = "heatindex"
STYPE_APPARENT_TEMP = "apparent_temperature"
STYPE_APPARENT_HUM = "apparent_humidity"
STYPE_DEWPOINT = "dewpoint"
STYPE_HUMIDI_STATE = "humidity_state"
STYPE_HEATINDEX_STATE = "heatindex_state"
STYPE_MOLD_INDICATOR = "mold_indicator"
STYPE_OUTSIDE_TEMP = "outside_temperature"
STYPE_WIND_SPEED = "wind_speed"

TRUNC = "trunc"
ROUND = "round"
CEIL = "ceil"

DECIAL_CALC_TYPE = [
    TRUNC,
    ROUND,
    CEIL,
]

SENSOR_TYPES = {
    STYPE_INSIDE_TEMP: [SensorDeviceClass.TEMPERATURE, '°C', 'mdi:thermometer'],
    STYPE_R_HUMIDI: [SensorDeviceClass.HUMIDITY, '%', 'mdi:water-percent'],
    STYPE_A_HUMIDI: [SensorDeviceClass.HUMIDITY, 'g/m³', 'mdi:water-percent'],
    STYPE_HEATINDEX: [SensorDeviceClass.TEMPERATURE, '°C', 'mdi:sun-thermometer'],
    STYPE_APPARENT_TEMP: [SensorDeviceClass.TEMPERATURE, '°C', 'mdi:thermometer'],
    STYPE_DEWPOINT: [SensorDeviceClass.TEMPERATURE, '°C', 'mdi:water-thermometer'],
    STYPE_HUMIDI_STATE: [DOMAIN + "__humidi_state", None, 'mdi:water-percent'],
    STYPE_HEATINDEX_STATE: [DOMAIN + "__heatindex_state", None, 'mdi:sun-thermometer'],
    STYPE_WIND_SPEED: [None, 'm/s', 'mdi:weather-windy'],
    STYPE_MOLD_INDICATOR: [SensorDeviceClass.HUMIDITY, '%', 'mdi:snowflake-alert'],
    STYPE_OUTSIDE_TEMP: [SensorDeviceClass.TEMPERATURE, '°C', 'mdi:thermometer'],
}

DEFAULT_LANG = "Korean"

