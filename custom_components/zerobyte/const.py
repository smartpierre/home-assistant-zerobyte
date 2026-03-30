"""Constants for the Zerobyte integration."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "zerobyte"

CONF_HOST = "host"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_VERIFY_SSL = "verify_ssl"

DEFAULT_SCAN_INTERVAL = 300  # 5 minutes
