"""Config flow for Hello World integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
from homeassistant.helpers import selector as st
from .const import *  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
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
                    #vol.Optional(CONF_SENSOR_LANGUAGE, default=DEFAULT_LANG): vol.In(TRANSLATION.keys()),
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
            vol.Required(CONF_INSIDE_TEMP_ENTITY, default=defaults.options.get(CONF_INSIDE_TEMP_ENTITY) if defaults.options.get(CONF_INSIDE_TEMP_ENTITY, None) else defaults.data.get(CONF_INSIDE_TEMP_ENTITY, None)
            ): selector({"entity": {"domain": ["sensor", "input_number"]}}),
            vol.Required(CONF_HUMIDITY_ENTITY, default=defaults.options.get(CONF_HUMIDITY_ENTITY, None) if defaults.options.get(CONF_HUMIDITY_ENTITY, None) else defaults.data.get(CONF_HUMIDITY_ENTITY, None)
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
            vol.Optional(CONF_MOLD_CALIB_FACTOR, default=defaults.options.get(CONF_MOLD_CALIB_FACTOR, 2.0)): vol.All(vol.Coerce(float), vol.Range(0, 20)),
            vol.Optional(CONF_DECIMAL_PLACES, default=defaults.options.get(CONF_DECIMAL_PLACES, 2.0)): vol.All(vol.Coerce(int), vol.Range(0, 5)),
            vol.Optional(CONF_DECIMAL_CALC_TYPE, default=defaults.options.get(CONF_DECIMAL_CALC_TYPE, TRUNC)): st.SelectSelector(st.SelectSelectorConfig(
                                                                                                    options=DECIAL_CALC_TYPE, 
                                                                                                    custom_value=False, 
                                                                                                    multiple=False,
                                                                                                    mode=st.SelectSelectorMode.DROPDOWN,
                                                                                                    translation_key=CONF_DECIMAL_CALC_TYPE
                                                                                                )
                                                                                            ),
        }
    )

class OptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry
        _LOGGER.debug("config_entries data : " + str(self.config_entry.data))

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Handle options flow."""
        conf = self.config_entry
        if conf.source == config_entries.SOURCE_IMPORT:
            return self.async_show_form(step_id="init", data_schema=None)
        if user_input is not None:
            _LOGGER.debug("before async_create_entry")
            self.hass.config_entries.async_update_entry(conf, data=
                {
                    CONF_DEVICE_NAME: conf.data[CONF_DEVICE_NAME],
                    CONF_INSIDE_TEMP_ENTITY: user_input.get(CONF_INSIDE_TEMP_ENTITY),
                    CONF_HUMIDITY_ENTITY: user_input.get(CONF_HUMIDITY_ENTITY)
                }
            )
            return self.async_create_entry(title=conf.data[CONF_DEVICE_NAME], data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_get_options_schema(self.config_entry),
        )

