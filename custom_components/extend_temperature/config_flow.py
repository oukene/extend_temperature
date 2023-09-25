"""Config flow for Hello World integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from types import MappingProxyType
from typing import Any
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
from .const import *  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

# This is the schema that used to display the UI to the user. This simple
# schema has a single required host field, but it could include a number of fields
# such as username, password etc. See other components in the HA core code for
# further examples.
# Note the input displayed to the user will be translated. See the
# translations/<lang>.json file and strings.json. See here for further information:
# https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#translations
# At the time of writing I found the translations created by the scaffold didn't
# quite work as documented and always gave me the "Lokalise key references" string
# (in square brackets), rather than the actual translated value. I did not attempt to
# figure this out or look further into it.


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This example uses PUSH, as the dummy hub will notify HA of
    # changes.
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # This goes through the steps to take the user through the setup process.
        # Using this it is possible to update the UI and prompt for additional
        # information. This example provides a single form (built from `DATA_SCHEMA`),
        # and when that has some validated input, it calls `async_create_entry` to
        # actually create the HA config entry. Note the "title" value is returned by
        # `validate_input` above.
        errors = {}
        
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_DEVICE_NAME], data=user_input)

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", 
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_NAME): str,
                    vol.Required(CONF_INSIDE_TEMP_ENTITY): selector({"entity": {}}),
                    vol.Required(CONF_HUMIDITY_ENTITY): selector({"entity": {}}),
                    vol.Optional(CONF_SENSOR_LANGUAGE, default=DEFAULT_LANG): vol.In(TRANSLATION.keys()),
                }
            ),
            errors=errors
        )

    async def async_step_import(self, user_input=None):
        """Handle configuration by yaml file."""
        await self.async_set_unique_id(user_input[CONF_DEVICE_NAME])
        for entry in self._async_current_entries():
            if entry.unique_id == self.unique_id:
                self.hass.config_entries.async_update_entry(entry, data=user_input)
                self._abort_if_unique_id_configured()
        return self.async_create_entry(title=user_input[CONF_DEVICE_NAME], data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle a option flow."""
        return OptionsFlowHandler(config_entry)


@callback  # type: ignore[misc]
def _get_options_schema(defaults) -> vol.Schema:
    """Return options schema."""
    _LOGGER.debug("defaults : " + str(defaults.options))
    return vol.Schema(
        {
            vol.Required(CONF_INSIDE_TEMP_ENTITY, default=defaults.data.get(CONF_INSIDE_TEMP_ENTITY, None)
            ): selector({"entity": {"domain": ["sensor", "input_number"]}}),
            vol.Required(CONF_HUMIDITY_ENTITY, default=defaults.data.get(CONF_HUMIDITY_ENTITY, None)
            ): selector({"entity": {"domain": ["sensor", "input_number"]}}),
            vol.Optional(
                CONF_OUTSIDE_TEMP_ENTITY, 
                description={
                    "suggested_value": defaults.options[CONF_OUTSIDE_TEMP_ENTITY]}
                if CONF_OUTSIDE_TEMP_ENTITY in defaults.options
                else None,
            ): selector({"entity": {"domain": ["sensor", "input_number"]}}),
            vol.Optional(CONF_APPARENT_TEMP_SOURCE_ENTITY, CONF_APPARENT_TEMP_SOURCE_ENTITY,
                         description={
                             "suggested_value": defaults.options[CONF_APPARENT_TEMP_SOURCE_ENTITY]}
                         if CONF_APPARENT_TEMP_SOURCE_ENTITY in defaults.options
                         else None,
            ): selector({"entity": {"domain": ["sensor", "input_number"]}}),
            vol.Optional(CONF_APPARENT_HUM_SOURCE_ENTITY, CONF_APPARENT_HUM_SOURCE_ENTITY,
                         description={
                             "suggested_value": defaults.options[CONF_APPARENT_HUM_SOURCE_ENTITY]}
                         if CONF_APPARENT_HUM_SOURCE_ENTITY in defaults.options
                         else None,
            ): selector({"entity": {"domain": ["sensor", "input_number"]}}),
            vol.Optional(CONF_WIND_ENTITY, CONF_WIND_ENTITY,
                         description={
                             "suggested_value": defaults.options[CONF_WIND_ENTITY]}
                         if CONF_WIND_ENTITY in defaults.options
                         else None,
            ): selector({"entity": {"domain": ["sensor", "input_number"]}}),
            vol.Optional(CONF_DECIMAL_PLACES, default=defaults.options.get(CONF_DECIMAL_PLACES, 2.0)): vol.All(vol.Coerce(int), vol.Range(0, 5)),
            vol.Optional(CONF_SENSOR_LANGUAGE, default=defaults.options.get(CONF_SENSOR_LANGUAGE, DEFAULT_LANG)): vol.In(TRANSLATION.keys()),
        }
    )

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Naver Weather."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Handle options flow."""
        conf = self.config_entry
        if conf.source == config_entries.SOURCE_IMPORT:
            return self.async_show_form(step_id="init", data_schema=None)
        if user_input is not None:
            _LOGGER.debug("before async_create_entry")
            return self.async_create_entry(title=conf.data[CONF_DEVICE_NAME], data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_get_options_schema(self.config_entry),
        )

