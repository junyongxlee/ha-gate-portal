"""HTTP API views for Gate Portal."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest, HTTPNotFound, HTTPUnauthorized
import voluptuous as vol

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    API_ACTION_PATH,
    API_STATUS_PATH,
    CONF_CORS_ORIGINS,
    CONF_ENABLED,
    CONF_ENTITIES,
    CONF_PIN_HASH,
    DOMAIN,
    PIN_HEADER,
    RATE_LIMIT_MAX_ATTEMPTS,
    RATE_LIMIT_WINDOW_SECONDS,
)
from .entity_actions import build_entity_info, call_entity_action, get_actions_for_entity
from .pin import verify_pin

_LOGGER = logging.getLogger(__name__)

ACTION_SCHEMA = vol.Schema(
    {
        vol.Required("pin"): str,
        vol.Required("entity_id"): str,
        vol.Required("action"): str,
    }
)


class RateLimiter:
    """Track failed PIN attempts per source IP."""

    def __init__(self) -> None:
        """Initialize rate limiter state."""
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def is_blocked(self, remote: str) -> bool:
        """Return whether the remote address is rate limited."""
        now = time.monotonic()
        attempts = self._prune(remote, now)
        return len(attempts) >= RATE_LIMIT_MAX_ATTEMPTS

    def record_failure(self, remote: str) -> None:
        """Record a failed PIN attempt."""
        now = time.monotonic()
        attempts = self._prune(remote, now)
        attempts.append(now)
        self._attempts[remote] = attempts

    def reset(self, remote: str) -> None:
        """Clear failed attempts for a remote address."""
        self._attempts.pop(remote, None)

    def _prune(self, remote: str, now: float) -> list[float]:
        """Remove expired attempts for a remote address."""
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS
        attempts = [ts for ts in self._attempts.get(remote, []) if ts > cutoff]
        self._attempts[remote] = attempts
        return attempts


def get_config_entry(hass: HomeAssistant) -> ConfigEntry | None:
    """Return the single Gate Portal config entry, if present."""
    entries = hass.config_entries.async_entries(DOMAIN)
    return entries[0] if entries else None


def get_rate_limiter(hass: HomeAssistant) -> RateLimiter:
    """Return the shared rate limiter for Gate Portal requests."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if "rate_limiter" not in domain_data:
        domain_data["rate_limiter"] = RateLimiter()
    return domain_data["rate_limiter"]


def get_cors_origin(request: web.Request, allowed_origins: list[str]) -> str | None:
    """Return the CORS origin to echo, if allowed."""
    origin = request.headers.get("Origin")
    if not origin:
        return None
    if not allowed_origins or origin in allowed_origins:
        return origin
    return None


def add_cors_headers(
    response: web.Response, request: web.Request, allowed_origins: list[str]
) -> web.Response:
    """Add CORS headers to a response."""
    origin = get_cors_origin(request, allowed_origins)
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = (
            f"Content-Type, {PIN_HEADER}"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def extract_pin(request: web.Request, body: dict[str, Any] | None = None) -> str | None:
    """Extract PIN from query, header, or JSON body."""
    if body and body.get("pin"):
        return str(body["pin"])
    header_pin = request.headers.get(PIN_HEADER)
    if header_pin:
        return header_pin
    query_pin = request.query.get("pin")
    if query_pin:
        return query_pin
    return None


def verify_request_pin(
    hass: HomeAssistant,
    request: web.Request,
    rate_limiter: RateLimiter,
    body: dict[str, Any] | None = None,
) -> ConfigEntry:
    """Validate portal state and PIN for a request."""
    entry = get_config_entry(hass)
    if entry is None:
        raise HTTPUnauthorized(text="Unauthorized")

    remote = request.remote or "unknown"
    if rate_limiter.is_blocked(remote):
        _LOGGER.warning("Rate limited PIN attempts from %s", remote)
        raise HTTPUnauthorized(text="Unauthorized")

    options = entry.options
    if not options.get(CONF_ENABLED, True):
        raise web.HTTPServiceUnavailable(
            text='{"enabled": false}',
            content_type="application/json",
        )

    pin_hash = options.get(CONF_PIN_HASH, "")
    pin = extract_pin(request, body)
    if not pin or not pin_hash or not verify_pin(pin, pin_hash):
        rate_limiter.record_failure(remote)
        _LOGGER.warning("Failed PIN validation from %s", remote)
        raise HTTPUnauthorized(text="Unauthorized")

    rate_limiter.reset(remote)
    return entry


class GatePortalBaseView(HomeAssistantView):
    """Shared helpers for Gate Portal views."""

    requires_auth = False
    cors_allowed = True

    def _json_response(
        self,
        request: web.Request,
        data: dict[str, Any],
        *,
        status: int = 200,
    ) -> web.Response:
        """Return a JSON response with CORS headers."""
        entry = get_config_entry(request.app["hass"])
        allowed_origins = []
        if entry is not None:
            allowed_origins = entry.options.get(CONF_CORS_ORIGINS, [])
        response = self.json(data, status_code=status)
        return add_cors_headers(response, request, allowed_origins)


class GatePortalStatusView(GatePortalBaseView):
    """Return portal status and exposed entity metadata."""

    url = API_STATUS_PATH
    name = "api:gate_portal:status"

    async def get(self, request: web.Request) -> web.Response:
        """Handle status requests."""
        hass: HomeAssistant = request.app["hass"]
        rate_limiter = get_rate_limiter(hass)

        try:
            entry = verify_request_pin(hass, request, rate_limiter)
        except web.HTTPServiceUnavailable as err:
            entry = get_config_entry(hass)
            allowed_origins = []
            if entry is not None:
                allowed_origins = entry.options.get(CONF_CORS_ORIGINS, [])
            response = web.Response(
                body=err.text.encode("utf-8"),
                status=err.status_code,
                content_type="application/json",
            )
            return add_cors_headers(response, request, allowed_origins)

        options = entry.options
        entities_out: list[dict[str, object]] = []
        for entity_id in options.get(CONF_ENTITIES, []):
            info = build_entity_info(hass, entity_id)
            if info is not None:
                entities_out.append(info)

        return self._json_response(
            request,
            {
                "enabled": options.get(CONF_ENABLED, True),
                "entities": entities_out,
            },
        )


class GatePortalActionView(GatePortalBaseView):
    """Execute an action on an exposed entity."""

    url = API_ACTION_PATH
    name = "api:gate_portal:action"

    async def post(self, request: web.Request) -> web.Response:
        """Handle action requests."""
        hass: HomeAssistant = request.app["hass"]
        rate_limiter = get_rate_limiter(hass)

        try:
            body = await request.json()
        except ValueError as err:
            raise HTTPBadRequest from err

        try:
            entry = verify_request_pin(hass, request, rate_limiter, body)
            data = ACTION_SCHEMA(body)
        except web.HTTPServiceUnavailable as err:
            entry = get_config_entry(hass)
            allowed_origins = []
            if entry is not None:
                allowed_origins = entry.options.get(CONF_CORS_ORIGINS, [])
            response = web.Response(
                body=err.text.encode("utf-8"),
                status=err.status_code,
                content_type="application/json",
            )
            return add_cors_headers(response, request, allowed_origins)
        except vol.Invalid as err:
            raise HTTPBadRequest from err

        entity_id = data["entity_id"]
        action = data["action"]
        allowed_entities = entry.options.get(CONF_ENTITIES, [])

        if entity_id not in allowed_entities:
            raise HTTPNotFound(text="Entity not found")

        if action not in get_actions_for_entity(entity_id):
            raise HTTPBadRequest(text="Invalid action for entity")

        try:
            await call_entity_action(hass, entity_id, action)
        except ValueError as err:
            raise HTTPBadRequest from err

        return self._json_response(
            request,
            {
                "success": True,
                "entity_id": entity_id,
                "action": action,
            },
        )
