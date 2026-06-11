"""Constants for the Gate Portal integration."""

DOMAIN = "gate_portal"

CONF_ENTITIES = "entities"
CONF_PIN = "pin"
CONF_PIN_HASH = "pin_hash"
CONF_ENABLED = "enabled"
CONF_CORS_ORIGINS = "cors_origins"

DEFAULT_ENABLED = True

API_STATUS_PATH = "/api/gate_portal/status"
API_ACTION_PATH = "/api/gate_portal/action"

PIN_HEADER = "X-Gate-Portal-Pin"
MIN_PIN_LENGTH = 4

RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 15 * 60

# domain -> list of supported action names
DOMAIN_ACTIONS: dict[str, list[str]] = {
    "cover": ["open", "close", "stop", "toggle"],
    "switch": ["on", "off", "toggle"],
    "lock": ["unlock", "lock"],
    "button": ["press"],
    "scene": ["activate"],
    "script": ["run"],
    "light": ["on", "off", "toggle"],
    "fan": ["on", "off", "toggle"],
    "input_boolean": ["on", "off", "toggle"],
    "valve": ["open", "close"],
    "garage_door": ["open", "close"],
}

# (domain, action) -> (service_domain, service_name)
ACTION_SERVICES: dict[tuple[str, str], tuple[str, str]] = {
    ("cover", "open"): ("cover", "open_cover"),
    ("cover", "close"): ("cover", "close_cover"),
    ("cover", "stop"): ("cover", "stop_cover"),
    ("cover", "toggle"): ("cover", "toggle_cover"),
    ("switch", "on"): ("switch", "turn_on"),
    ("switch", "off"): ("switch", "turn_off"),
    ("switch", "toggle"): ("switch", "toggle"),
    ("lock", "unlock"): ("lock", "unlock"),
    ("lock", "lock"): ("lock", "lock"),
    ("button", "press"): ("button", "press"),
    ("scene", "activate"): ("scene", "turn_on"),
    ("script", "run"): ("script", "turn_on"),
    ("light", "on"): ("light", "turn_on"),
    ("light", "off"): ("light", "turn_off"),
    ("light", "toggle"): ("light", "toggle"),
    ("fan", "on"): ("fan", "turn_on"),
    ("fan", "off"): ("fan", "turn_off"),
    ("fan", "toggle"): ("fan", "toggle"),
    ("input_boolean", "on"): ("input_boolean", "turn_on"),
    ("input_boolean", "off"): ("input_boolean", "turn_off"),
    ("input_boolean", "toggle"): ("input_boolean", "toggle"),
    ("valve", "open"): ("valve", "open_valve"),
    ("valve", "close"): ("valve", "close_valve"),
    ("garage_door", "open"): ("cover", "open_cover"),
    ("garage_door", "close"): ("cover", "close_cover"),
}
