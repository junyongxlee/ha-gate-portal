"""The Gate Portal integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .api import (
    GatePortalActionView,
    GatePortalStatusView,
    get_rate_limiter,
)
from .const import API_STATUS_PATH, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = []


def _route_is_registered(hass: HomeAssistant, path: str) -> bool:
    """Return whether an HTTP route is already registered for path."""
    for route in hass.http.app.router.routes():
        resource = getattr(route, "resource", None)
        if resource is not None and resource.canonical == path:
            return True
    return False


def _ensure_views_registered(hass: HomeAssistant) -> None:
    """Register HTTP views once, even across config entry reloads."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("views_registered"):
        return

    if _route_is_registered(hass, API_STATUS_PATH):
        domain_data["views_registered"] = True
        get_rate_limiter(hass)
        return

    get_rate_limiter(hass)
    hass.http.register_view(GatePortalStatusView())
    hass.http.register_view(GatePortalActionView())
    domain_data["views_registered"] = True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Gate Portal integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gate Portal from a config entry."""
    _ensure_views_registered(hass)

    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[entry.entry_id] = {"entry": entry}

    _LOGGER.debug("Gate Portal entry %s set up", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    domain_data = hass.data.get(DOMAIN)
    if domain_data:
        domain_data.pop(entry.entry_id, None)
        # Keep rate_limiter, views_registered, and HTTP routes for reloads.

    _LOGGER.debug("Gate Portal entry %s unloaded", entry.entry_id)
    return True
