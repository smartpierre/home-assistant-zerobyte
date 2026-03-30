"""Zerobyte API Client."""

from __future__ import annotations

import socket
from http.cookies import SimpleCookie
from typing import Any

import aiohttp
import async_timeout

from .const import LOGGER


class ZerobyteApiClientError(Exception):
    """General API error."""


class ZerobyteApiClientCommunicationError(ZerobyteApiClientError):
    """Communication error (timeout, network)."""


class ZerobyteApiClientAuthenticationError(ZerobyteApiClientError):
    """Authentication error (invalid credentials, expired session)."""


class ZerobyteApiClient:
    """Client for the Zerobyte REST API using cookie-based auth."""

    def __init__(
        self,
        host: str,
        email: str,
        password: str,
        session: aiohttp.ClientSession,
        verify_ssl: bool = True,
    ) -> None:
        self._host = host.rstrip("/")
        self._email = email
        self._password = password
        self._session = session
        self._verify_ssl = verify_ssl
        self._cookies: dict[str, str] = {}

    async def async_login(self) -> None:
        """Authenticate and store the session cookie."""
        url = f"{self._host}/api/auth/sign-in/email"
        try:
            async with async_timeout.timeout(10):
                ssl = None if self._verify_ssl else False
                response = await self._session.post(
                    url,
                    json={"email": self._email, "password": self._password},
                    ssl=ssl,
                )
                if response.status in (401, 403):
                    body = await response.json()
                    msg = body.get("message", "Invalid credentials")
                    raise ZerobyteApiClientAuthenticationError(msg)
                response.raise_for_status()

                self._extract_cookies(response)
                if not self._cookies:
                    msg = "No session cookie received after login"
                    raise ZerobyteApiClientAuthenticationError(msg)

        except ZerobyteApiClientAuthenticationError:
            raise
        except TimeoutError as exc:
            raise ZerobyteApiClientCommunicationError(
                f"Timeout connecting to {self._host}"
            ) from exc
        except (aiohttp.ClientError, socket.gaierror) as exc:
            raise ZerobyteApiClientCommunicationError(
                f"Error connecting to {self._host}: {exc}"
            ) from exc

    def _extract_cookies(self, response: aiohttp.ClientResponse) -> None:
        """Extract session cookies from a response."""
        for header_value in response.headers.getall("Set-Cookie", []):
            cookie: SimpleCookie = SimpleCookie()
            cookie.load(header_value)
            for key, morsel in cookie.items():
                self._cookies[key] = morsel.value

    async def _api_request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        retry_auth: bool = True,
    ) -> Any:
        """Make an authenticated API request with auto-reauth on 401."""
        url = f"{self._host}{path}"
        try:
            async with async_timeout.timeout(30):
                ssl = None if self._verify_ssl else False
                response = await self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    cookies=self._cookies,
                    ssl=ssl,
                )

                if response.status in (401, 403) and retry_auth:
                    LOGGER.debug("Session expired, re-authenticating")
                    await self.async_login()
                    return await self._api_request(
                        method, path, data, retry_auth=False
                    )

                if response.status in (401, 403):
                    raise ZerobyteApiClientAuthenticationError(
                        "Authentication failed after re-login"
                    )

                response.raise_for_status()
                self._extract_cookies(response)
                return await response.json()

        except (
            ZerobyteApiClientAuthenticationError,
            ZerobyteApiClientCommunicationError,
        ):
            raise
        except TimeoutError as exc:
            raise ZerobyteApiClientCommunicationError(
                f"Timeout fetching {path}"
            ) from exc
        except (aiohttp.ClientError, socket.gaierror) as exc:
            raise ZerobyteApiClientCommunicationError(
                f"Error fetching {path}: {exc}"
            ) from exc

    async def async_get_volumes(self) -> list[dict[str, Any]]:
        """Fetch all volumes."""
        return await self._api_request("GET", "/api/v1/volumes")

    async def async_get_repositories(self) -> list[dict[str, Any]]:
        """Fetch all repositories."""
        return await self._api_request("GET", "/api/v1/repositories")

    async def async_get_repository_stats(
        self, short_id: str
    ) -> dict[str, Any]:
        """Fetch storage and compression statistics for a repository."""
        return await self._api_request(
            "GET", f"/api/v1/repositories/{short_id}/stats"
        )

    async def async_get_backups(self) -> list[dict[str, Any]]:
        """Fetch all backup schedules."""
        return await self._api_request("GET", "/api/v1/backups")
