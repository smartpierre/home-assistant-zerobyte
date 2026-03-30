"""Config flow for the Zerobyte integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    ZerobyteApiClient,
    ZerobyteApiClientAuthenticationError,
    ZerobyteApiClientCommunicationError,
    ZerobyteApiClientError,
)
from .const import CONF_EMAIL, CONF_HOST, CONF_PASSWORD, CONF_VERIFY_SSL, DOMAIN, LOGGER


class ZerobyteFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zerobyte."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._test_connection(user_input)
            except ZerobyteApiClientAuthenticationError as exc:
                LOGGER.warning(exc)
                errors["base"] = "auth"
            except ZerobyteApiClientCommunicationError as exc:
                LOGGER.error(exc)
                errors["base"] = "connection"
            except ZerobyteApiClientError as exc:
                LOGGER.exception(exc)
                errors["base"] = "unknown"
            else:
                host = user_input[CONF_HOST].rstrip("/")
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Zerobyte ({host})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(
                            CONF_HOST, vol.UNDEFINED
                        ),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.URL,
                        ),
                    ),
                    vol.Required(
                        CONF_EMAIL,
                        default=(user_input or {}).get(CONF_EMAIL, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.EMAIL,
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                    vol.Optional(
                        CONF_VERIFY_SSL,
                        default=(user_input or {}).get(CONF_VERIFY_SSL, True),
                    ): selector.BooleanSelector(),
                },
            ),
            errors=errors,
        )

    async def _test_connection(self, user_input: dict[str, Any]) -> None:
        """Validate credentials by logging in and fetching data."""
        client = ZerobyteApiClient(
            host=user_input[CONF_HOST],
            email=user_input[CONF_EMAIL],
            password=user_input[CONF_PASSWORD],
            session=async_create_clientsession(self.hass),
            verify_ssl=user_input.get(CONF_VERIFY_SSL, True),
        )
        await client.async_login()
        await client.async_get_backups()
