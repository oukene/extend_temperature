"""Constants for the Detailed Hello World Push integration."""
from typing import DefaultDict
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import DEVICE_CLASS_TEMPERATURE, PLATFORM_SCHEMA

from homeassistant.const import (
    ATTR_TEMPERATURE, DEVICE_CLASS_TEMPERATURE,DEVICE_CLASS_HUMIDITY,
)


# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "extend_temperature"
VERSION = "1.2.0"

CONF_DEVICE_NAME = "device_name"
CONF_INSIDE_TEMP_ENTITY = 'inside_temp_entity'
CONF_HUMIDITY_ENTITY = 'humidity_entity'
CONF_OUTSIDE_TEMP_ENTITY = "outside_temp_entity"
CONF_WIND_ENTITY = 'wind_entity'
CONF_MOLD_CALIB_FACTOR = "mold_calib_factor"
CONF_APPARENT_TEMP_SOURCE_ENTITY = "apparent_temp_source_entity"
CONF_DECIMAL_PLACES = "decial_places"
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
STYPE_DEWPOINT = "dewpoint"
STYPE_HUMIDI_STATE = "humidity_state"
STYPE_HEATINDEX_STATE = "heatindex_state"
STYPE_MOLD_INDICATOR = "mold_indicator"
STYPE_OUTSIDE_TEMP = "outside_temperature"
STYPE_WIND_SPEED = "wind_speed"

SENSOR_TYPES = {
    STYPE_INSIDE_TEMP: [DEVICE_CLASS_TEMPERATURE, '°C'],
    STYPE_R_HUMIDI: [DEVICE_CLASS_HUMIDITY, '%'],
    STYPE_A_HUMIDI: [DEVICE_CLASS_HUMIDITY, 'g/m³'],
    STYPE_HEATINDEX: [DEVICE_CLASS_TEMPERATURE, '°C'],
    STYPE_APPARENT_TEMP: [DEVICE_CLASS_TEMPERATURE, '°C'],
    STYPE_DEWPOINT: [DEVICE_CLASS_TEMPERATURE, '°C'],
    STYPE_HUMIDI_STATE: [DOMAIN + "__humidi_state", None],
    STYPE_HEATINDEX_STATE: [DOMAIN + "__heatindex_state", None],
    STYPE_WIND_SPEED: [None, 'm/s'],
    STYPE_MOLD_INDICATOR:[DEVICE_CLASS_HUMIDITY, '%'],
    STYPE_OUTSIDE_TEMP:[DEVICE_CLASS_TEMPERATURE, '°C'],
}

DEFAULT_LANG = "Korean"

TRANSLATION = {
    "Korean": {
        STYPE_INSIDE_TEMP: "내부 온도",
        STYPE_R_HUMIDI: "상대 습도",
        STYPE_A_HUMIDI: "절대 습도",
        STYPE_HEATINDEX: "열 지수",
        STYPE_APPARENT_TEMP: "체감 온도",
        STYPE_DEWPOINT: "이슬점",
        STYPE_HUMIDI_STATE: "습도 상태",
        STYPE_HEATINDEX_STATE: "열지수 상태",
        STYPE_WIND_SPEED: "풍속",
        STYPE_MOLD_INDICATOR: "결로 지수",
        STYPE_OUTSIDE_TEMP: "외부 온도",
    },
    "English": {
        STYPE_INSIDE_TEMP: "Inside Temperature",
        STYPE_R_HUMIDI: "Relative Humidity",
        STYPE_A_HUMIDI: "Absolute Humidity",
        STYPE_HEATINDEX: "HeatIndex",
        STYPE_APPARENT_TEMP: "Apparent Temperature",
        STYPE_DEWPOINT: "Dewpoint",
        STYPE_HUMIDI_STATE: "Humidity State",
        STYPE_HEATINDEX_STATE: "HeatIndex State",
        STYPE_WIND_SPEED: "Wind Speed",
        STYPE_MOLD_INDICATOR: "Mold Indicator",
        STYPE_OUTSIDE_TEMP: "Outside Temperature",
    }
}

OPTIONS = [
    #(CONF_DEVICE_NAME, "", cv.string),
    (CONF_INSIDE_TEMP_ENTITY, "", cv.string),
    (CONF_HUMIDITY_ENTITY, "", cv.string),
    (CONF_OUTSIDE_TEMP_ENTITY, "", cv.string),
    (CONF_APPARENT_TEMP_SOURCE_ENTITY, "", cv.string),
    (CONF_WIND_ENTITY, "", cv.string),
    (CONF_MOLD_CALIB_FACTOR, "2.0", cv.string),
    (CONF_DECIMAL_PLACES, "2", vol.All(vol.Coerce(int), vol.Range(0, 5))),
    (CONF_SENSOR_LANGUAGE, DEFAULT_LANG, vol.In(TRANSLATION.keys())),
]
