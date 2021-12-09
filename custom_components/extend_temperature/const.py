"""Constants for the Detailed Hello World Push integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    ATTR_TEMPERATURE, DEVICE_CLASS_TEMPERATURE,DEVICE_CLASS_HUMIDITY,
)


# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "extend_temperature"
VERSION = "0.0.1"

CONF_DEVICE_NAME = "device_name"
CONF_INDOOR_TEMP_ENTITY = 'indoor_temp_entity'
CONF_HUMIDITY_ENTITY = 'humidity_entity'
CONF_OUTDOOR_TEMP_ENTITY = "outdoor_temp_entity"
CONF_WIND_ENTITY = 'wind_entity'
CONF_MOLD_CALIB_FACTOR = "mold_calib_factor"

ATTR_HUMIDITY = 'humidity'
ATTR_WIND = 'wind'
ATTR_INDOOR_TEMPERATURE = "indoor temperature"
ATTR_OUTDOOR_TEMPERATURE = "outdoor temperature"

OPTIONS = [
    #(CONF_DEVICE_NAME, "", cv.string),
    (CONF_INDOOR_TEMP_ENTITY, "", cv.string),
    (CONF_HUMIDITY_ENTITY, "", cv.string),
    (CONF_OUTDOOR_TEMP_ENTITY, "", cv.string),
    (CONF_WIND_ENTITY, "", cv.string),
    (CONF_MOLD_CALIB_FACTOR, 2, vol.All(vol.Coerce(float), vol.Range(min=1, max=20))),
]


STYPE_INDOOR_TEMP = "indoor_temperature"
STYPE_R_HUMIDI = "relative_humidity"
STYPE_A_HUMIDI = "absolute_humidity"
STYPE_HEATINDEX = "heatindex"
STYPE_APPARENT_TEMP = "apparent_temperature"
STYPE_DEWPOINT = "dewpoint"
STYPE_HUMIDI_STATE = "humidity_state"
STYPE_HEATINDEX_STATE = "heatindex_state"
STYPE_MOLD_INDICATOR = "mold_indicator"
STYPE_OUTDOOR_TEMP = "outdoor_temperature"
STYPE_WIND_SPEED = "wind_speed"

SENSOR_TYPES = {
    STYPE_INDOOR_TEMP: [DEVICE_CLASS_TEMPERATURE, '°C'],
    STYPE_R_HUMIDI: [DEVICE_CLASS_HUMIDITY, '%'],
    STYPE_A_HUMIDI: [DEVICE_CLASS_HUMIDITY, 'g/m³'],
    STYPE_HEATINDEX: [DEVICE_CLASS_TEMPERATURE, '°C'],
    STYPE_APPARENT_TEMP: [DEVICE_CLASS_TEMPERATURE, '°C'],
    STYPE_DEWPOINT: [DEVICE_CLASS_TEMPERATURE, '°C'],
    STYPE_HUMIDI_STATE: [DOMAIN + "__humidi_state", None],
    STYPE_HEATINDEX_STATE: [DOMAIN + "__heatindex_state", None],
    STYPE_WIND_SPEED: [None, 'm/s'],
    STYPE_MOLD_INDICATOR:[DEVICE_CLASS_HUMIDITY, '%'],
    STYPE_OUTDOOR_TEMP:[DEVICE_CLASS_TEMPERATURE, '°C'],
}

TRANSLATION = {
    "ko": {
        STYPE_INDOOR_TEMP: "온도",
        STYPE_R_HUMIDI: "상대습도",
        STYPE_A_HUMIDI: "절대습도",
        STYPE_HEATINDEX: "열지수",
        STYPE_APPARENT_TEMP: "체감 온도",
        STYPE_DEWPOINT: "이슬점",
        STYPE_HUMIDI_STATE: "습도 상태",
        STYPE_HEATINDEX_STATE: "열지수 상태",
        STYPE_WIND_SPEED: "풍속",
        STYPE_MOLD_INDICATOR: "결로지수",
        STYPE_OUTDOOR_TEMP: "실외온도",
    },
    "en": {
        STYPE_INDOOR_TEMP: "Indoor Temperature",
        STYPE_R_HUMIDI: "Relative Humidity",
        STYPE_A_HUMIDI: "Absolute Humidity",
        STYPE_HEATINDEX: "HeatIndex",
        STYPE_APPARENT_TEMP: "Apparent Temperature",
        STYPE_DEWPOINT: "Dewpoint",
        STYPE_HUMIDI_STATE: "Humidity State",
        STYPE_HEATINDEX_STATE: "HeatIndex State",
        STYPE_WIND_SPEED: "Wind Speed",
        STYPE_MOLD_INDICATOR: "Mold Indicator",
        STYPE_OUTDOOR_TEMP: "Outdoor Temperature",
    }
}

