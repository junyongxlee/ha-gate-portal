"""Config flow for Gate Portal."""

from __future__ import annotations

from collections.abc import Mapping
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


def _build_schema(
    options: Mapping[str, Any],
    *,
    require_pin: bool = False,
) -> vol.Schema:
    """Build the shared configuration schema."""
    current_entities = options.get(CONF_ENTITIES, [])
    pin_selector = selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
    )

    return vol.Schema(
        {
            vol.Required(
                CONF_ENTITIES,
                description={"suggested_value": current_entities},
            ): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True)),
            (
                vol.Required(CONF_PIN)
                if require_pin
                else vol.Optional(CONF_PIN, description={"suggested_value": ""})
            ): pin_selector,
            vol.Required(
                CONF_ENABLED,
                default=options.get(CONF_ENABLED, DEFAULT_ENABLED),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_CORS_ORIGINS,
                description={"suggested_value": options.get(CONF_CORS_ORIGINS, [])},
            ): selector.TextSelector(selector.TextSelectorConfig(multiple=True)),
        }
    )


def _validate_options(
    user_input: dict[str, Any],
    existing_options: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, Any] | None]:
    """Validate input and return option updates when valid."""
    errors: dict[str, str] = {}
    enabled = user_input[CONF_ENABLED]
    entities = user_input.get(CONF_ENTITIES) or []
    pin = user_input.get(CONF_PIN) or ""
    existing_hash = existing_options.get(CONF_PIN_HASH, "")

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
        return {}, new_options

    return errors, None


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
            errors, new_options = _validate_options(user_input, {})
            if errors:
                return self.async_show_form(
                    step_id="user",
                    data_schema=_build_schema({}, require_pin=True),
                    errors=errors,
                )
            return self.async_create_entry(
                title="Gate Portal",
                data={},
                options=new_options,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema({}, require_pin=True),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> GatePortalOptionsFlow:
        """Get the options flow for this handler."""
        return GatePortalOptionsFlow()


class GatePortalOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle options flow for Gate Portal."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Gate Portal options."""
        options = self.config_entry.options

        if user_input is not None:
            errors, new_options = _validate_options(user_input, options)
            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=_build_schema(options),
                    errors=errors,
                )
            return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(options),
        )
