"""Config flow for Gate Portal."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_CORS_ORIGINS,
    CONF_ENABLED,
    CONF_ENTITIES,
    CONF_PIN,
    CONF_PIN_HASH,
    DEFAULT_ENABLED,
    DOMAIN,
    MIN_PIN_LENGTH,
)
from .pin import hash_pin


class GatePortalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gate Portal."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            return self.async_create_entry(title="Gate Portal", data={})

        return self.async_show_form(step_id="user")


class GatePortalOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle options flow for Gate Portal."""

    def _options_schema(self) -> vol.Schema:
        """Build the options schema with suggested values."""
        options = self.config_entry.options
        current_entities = options.get(CONF_ENTITIES, [])

        return vol.Schema(
            {
                vol.Required(
                    CONF_ENTITIES,
                    description={"suggested_value": current_entities},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(multiple=True)
                ),
                vol.Optional(CONF_PIN): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(
                    CONF_ENABLED,
                    default=options.get(CONF_ENABLED, DEFAULT_ENABLED),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_CORS_ORIGINS,
                    description={
                        "suggested_value": options.get(CONF_CORS_ORIGINS, [])
                    },
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiple=True)
                ),
            }
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Gate Portal options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            enabled = user_input[CONF_ENABLED]
            entities = user_input.get(CONF_ENTITIES) or []
            pin = user_input.get(CONF_PIN) or ""
            existing_hash = self.config_entry.options.get(CONF_PIN_HASH, "")

            if enabled and not entities:
                errors["base"] = "entities_required"
            elif pin and len(pin) < MIN_PIN_LENGTH:
                errors["base"] = "pin_too_short"
            elif not existing_hash and not pin:
                errors["base"] = "pin_required"
            else:
                new_options = {
                    CONF_ENTITIES: entities,
                    CONF_ENABLED: enabled,
                    CONF_CORS_ORIGINS: user_input.get(CONF_CORS_ORIGINS) or [],
                    CONF_PIN_HASH: existing_hash,
                }
                if pin:
                    new_options[CONF_PIN_HASH] = hash_pin(pin)

                return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="init",
            data_schema=self._options_schema(),
            errors=errors,
        )


@callback
def async_get_options_flow(
    config_entry: config_entries.ConfigEntry,
) -> GatePortalOptionsFlow:
    """Get the options flow for this handler."""
    return GatePortalOptionsFlow(config_entry)
